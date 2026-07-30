import streamlit as st
import os
import io
import logging
import pypdf

# Suppress pypdf warning logs (e.g., incorrect startxref pointer)
logging.getLogger("pypdf").setLevel(logging.ERROR)
import openai
from pydantic import BaseModel, Field
from career_assistant import db

# Load .env file at project root
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.abspath(os.path.join(current_dir, "..", "..", ".env"))
if os.path.exists(env_path):
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip().strip('"').strip("'")

# Define Pydantic models for OpenAI Structured Outputs
class ResumeBuilderResponse(BaseModel):
    explanation: str = Field(description="A friendly, concise explanation of the edits made to the resume.")
    updated_resume_markdown: str = Field(description="The complete, updated resume formatted in Markdown.")

def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return openai.OpenAI(api_key=api_key)

def extract_all_text_from_pdf(pdf_bytes):
    if not pdf_bytes:
        return ""
    try:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""

def generate_initial_markdown_from_text(raw_text, full_name, desired_role, location):
    client = get_openai_client()
    if not client:
        return ""
        
    system_prompt = (
        "You are an expert resume writer. Your task is to take a raw text extraction of a user's resume "
        "and format it into a beautiful, professional, and structured Markdown resume.\n"
        "Organize it logically with clear headers (e.g. # Name, ## Professional Summary, ## Experience, "
        "## Education, ## Skills, ## Projects). Clean up any formatting artifacts. "
        "Do not include any intro, outro, or markdown code block wrapper (like ```markdown), just return raw markdown content."
    )
    
    user_prompt = f"Name: {full_name}\nTarget Role: {desired_role}\nLocation: {location}\n\nRaw Resume Text:\n{raw_text}"
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating initial markdown: {e}")
        return ""

def generate_skeleton_markdown(full_name, desired_role, location, skills):
    skills_list = ", ".join([s.strip() for s in skills.split(",") if s.strip()]) if skills else "N/A"
    return f"""# {full_name}
Target Role: {desired_role} | Location: {location}

## 🎯 Professional Summary
A motivated and goal-oriented professional looking to excel as a {desired_role}.

## 🛠️ Skills
{skills_list}

## 💼 Work Experience
**Company Name** | *Job Title* (Dates)
- Describe your key achievements and responsibilities.
- Use action verbs and highlight quantitative metrics.

## 🎓 Education
**Degree Name** | *University Name* (Graduation Year)
- Details or GPA (Optional).

## 🚀 Projects
**Project Name**
- Brief description of what you built and the impact it had.
"""

def process_resume_edit_request(current_markdown, user_request, profile_info):
    client = get_openai_client()
    if not client:
        return "OpenAI client is not configured. Please check your API key.", current_markdown
        
    system_prompt = (
        "You are an agentic AI Resume Editor. Your goal is to help the user edit and improve their resume.\n"
        "You must accept the current resume (in Markdown format) and the user's edit request, and perform the requested edits.\n"
        "Ensure the resulting resume is structured in clean Markdown.\n"
        "You must return two things:\n"
        "1. A friendly, brief explanation of the changes you made (explaining why you made them or highlighting specific additions).\n"
        "2. The full, complete updated resume in Markdown format.\n"
        "Maintain a highly professional and tailored tone suitable for the user's target role."
    )
    
    user_prompt = (
        f"Target Role: {profile_info.get('desired_role', '')}\n"
        f"User Edit Request: {user_request}\n\n"
        f"Current Resume Markdown:\n"
        f"{current_markdown}"
    )
    
    try:
        response = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format=ResumeBuilderResponse,
            temperature=0.2
        )
        parsed = response.choices[0].message.parsed
        return parsed.explanation, parsed.updated_resume_markdown
    except Exception as e:
        return f"Error processing edit request: {str(e)}", current_markdown

def sync_skills_from_resume_markdown(markdown_text):
    client = get_openai_client()
    if not client:
        return ""
        
    system_prompt = (
        "You are an expert resume parser. Extract a comma-separated list of professional skills "
        "present in the following resume. Return ONLY a comma-separated list of skills (e.g. Python, SQL, Project Management). "
        "Do not include any intro, outro, or markdown code block formatting."
    )
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": markdown_text}
            ],
            temperature=0.1
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error syncing skills: {e}")
        return ""

def render_resume_builder():
    st.markdown("### 📝 AI Resume Editor")
    
    # Initialize and check API key
    if not os.getenv("OPENAI_API_KEY"):
        if "openai_api_key" in st.session_state:
            os.environ["OPENAI_API_KEY"] = st.session_state.openai_api_key
        else:
            st.warning("⚠️ OpenAI API Key is missing. Please add it to your `.env` file or enter it below to proceed:")
            key_input = st.text_input("OpenAI API Key", type="password", key="openai_key_input")
            if st.button("Save API Key 🔑", key="btn_save_key"):
                if key_input.strip():
                    st.session_state.openai_api_key = key_input.strip()
                    os.environ["OPENAI_API_KEY"] = key_input.strip()
                    st.success("API key saved for this session!")
                    st.rerun()
            st.stop()

    profile = db.get_profile()
    if not profile:
        st.info("Please complete onboarding first.")
        st.stop()
        
    # Get current resume markdown
    current_resume = profile.get("resume_markdown")
    
    # Initialize if empty
    if not current_resume:
        with st.spinner("Initializing your resume..."):
            if profile.get("resume_bytes"):
                raw_text = extract_all_text_from_pdf(profile["resume_bytes"])
                if raw_text.strip():
                    current_resume = generate_initial_markdown_from_text(
                        raw_text,
                        profile["full_name"],
                        profile["desired_role"],
                        profile["location"]
                    )
                    
            if not current_resume or not current_resume.strip():
                current_resume = generate_skeleton_markdown(
                    profile["full_name"],
                    profile["desired_role"],
                    profile["location"],
                    profile["skills"]
                )
                
            db.update_resume_markdown(current_resume)
            
    # Initialize chat history
    if "resume_chat_history" not in st.session_state:
        st.session_state.resume_chat_history = [
            {
                "role": "assistant",
                "content": f"Hi {profile['full_name'].split()[0]}! I've loaded your resume in the preview pane. Let me know what edits you'd like to make (e.g. 'rewrite my summary', 'add Python skill', 'improve my experience section')."
            }
        ]
        
    # Layout split
    col_chat, col_preview = st.columns([5, 5])
    
    with col_chat:
        st.markdown("#### 💬 Edit Chatbox")
        
        # Scrollable container for chat history
        chat_container = st.container(height=420)
        with chat_container:
            for idx, msg in enumerate(st.session_state.resume_chat_history):
                with st.chat_message(msg["role"]):
                    col_text, col_del = st.columns([9, 1])
                    with col_text:
                        st.write(msg["content"])
                    with col_del:
                        if st.button("🗑️", key=f"del_res_msg_{idx}", type="secondary", help="Delete message"):
                            st.session_state.resume_chat_history.pop(idx)
                            st.rerun()
                            
        # Chat input
        if user_input := st.chat_input("Tell the AI to edit your resume...", key="resume_chat_input"):
            st.session_state.resume_chat_history.append({"role": "user", "content": user_input})
            st.session_state.awaiting_resume_response = True
            st.rerun()
            
        if st.session_state.get("awaiting_resume_response", False):
            st.session_state.awaiting_resume_response = False
            user_msg = st.session_state.resume_chat_history[-1]["content"]
            
            with st.chat_message("assistant"):
                with st.spinner("AI is editing your resume..."):
                    explanation, updated_markdown = process_resume_edit_request(
                        current_resume,
                        user_msg,
                        profile
                    )
                    db.update_resume_markdown(updated_markdown)
                    current_resume = updated_markdown
                    
                st.session_state.resume_chat_history.append({
                    "role": "assistant",
                    "content": explanation
                })
                st.rerun()
                
    with col_preview:
        st.markdown("#### 📄 Live Resume Preview")
        
        # Render markdown resume inside container
        with st.container(border=True, height=420):
            st.markdown(current_resume)
            
        st.markdown("<div style='margin-bottom: 0.6rem;'></div>", unsafe_allow_html=True)
        col_dl, col_sync, col_reset = st.columns([1, 1, 1])
        
        with col_dl:
            st.download_button(
                label="📥 Download Resume",
                data=current_resume,
                file_name=f"Resume_{profile['full_name'].replace(' ', '_')}.md",
                mime="text/markdown",
                use_container_width=True
            )
            
        with col_sync:
            if st.button("🔄 Sync Skills", help="Extract and update skills on dashboard from this resume", use_container_width=True):
                with st.spinner("Extracting skills..."):
                    new_skills = sync_skills_from_resume_markdown(current_resume)
                    if new_skills:
                        db.save_profile(
                            full_name=profile["full_name"],
                            desired_role=profile["desired_role"],
                            location=profile["location"],
                            resume_name=profile["resume_name"],
                            resume_bytes=profile["resume_bytes"],
                            skills=new_skills
                        )
                        st.session_state.skills = new_skills
                        st.success("Dashboard skills synced!")
                        st.rerun()
                        
        with col_reset:
            # We use an expander or confirmation button for reset to prevent accidental clicks
            if st.button("⚠️ Reset Resume", help="Reset to original uploaded version", use_container_width=True):
                db.update_resume_markdown(None)
                st.session_state.resume_chat_history = [
                    {
                        "role": "assistant",
                        "content": "Resume reset successfully! I've re-initialized it from your profile."
                    }
                ]
                st.rerun()
