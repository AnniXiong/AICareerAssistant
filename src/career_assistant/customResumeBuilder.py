import streamlit as st
import os
import requests
import re
from bs4 import BeautifulSoup
from career_assistant import db
import importlib
importlib.reload(db)

def strip_highlights(text):
    if not text:
        return ""
    return re.sub(r'</?mark[^>]*>', '', text)




def extract_job_description_from_url(url):
    if not url or not url.strip().startswith("http"):
        return None, "Invalid or missing URL."
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None, f"Failed to fetch webpage (Status Code: {response.status_code})."
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove script, style, head, header, footer, nav tags
        for element in soup(["script", "style", "head", "header", "footer", "nav"]):
            element.decompose()
            
        # Get clean text
        text = soup.get_text(separator="\n")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        cleaned_text = "\n".join(lines)
        return cleaned_text, None
    except Exception as e:
        return None, str(e)

def format_job_description_with_ai(raw_text):
    from career_assistant.ResumeBuilder import get_openai_client
    client = get_openai_client()
    if not client:
        return raw_text
        
    system_prompt = (
        "You are an expert job recruiter and career assistant.\n"
        "Your task is to take a raw web page text extraction of a job posting and format it into a clean, structured job description in Markdown.\n"
        "Organize it logically with clear headers (e.g. ## Role Overview, ## Key Responsibilities, ## Requirements, ## Preferred Skills).\n"
        "Exclude unrelated website headers, footers, cookie notices, and navigation text.\n"
        "If the raw text is too messy or short, do your best to salvage the core job details."
    )
    
    user_prompt = f"Raw Job Posting Text:\n{raw_text[:8000]}"
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error formatting job description with AI: {e}")
        return raw_text

def tailor_resume_with_ai(resume_markdown, job_description, target_role, company_name):
    from career_assistant.ResumeBuilder import get_openai_client
    client = get_openai_client()
    if not client:
        return None, "OpenAI API Key is not configured."
        
    system_prompt = (
        "You are an expert resume writer and career coach.\n"
        "Your goal is to tailor the user's resume (in Markdown format) to match a specific job description.\n"
        "Align their professional summary, highlight their relevant skills, and rewrite/emphasize details in their work experience "
        "and projects to highlight alignment with the job's key requirements, while keeping the content truthful and realistic.\n"
        "Crucially, you must highlight the parts of the resume that you changed, added, or tailored by wrapping them in `<mark style='background-color: #FFF2CC; color: #000000; border-radius: 4px; padding: 0px 4px;'>...</mark>` tags.\n"
        "Do not wrap entire sections in a single tag unless the entire section was newly written; highlight the specific sentences, words, or bullets that were modified or added.\n"
        "Ensure the resulting resume is structured in clean Markdown.\n"
        "Return ONLY the updated Markdown resume content. Do not include any intro, outro, or markdown code block wrapper (like ```markdown), just return raw markdown content."
    )
    
    user_prompt = (
        f"Company Name: {company_name}\n"
        f"Target Role: {target_role}\n\n"
        f"Job Description:\n{job_description}\n\n"
        f"Current Resume Markdown:\n{resume_markdown}"
    )
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content.strip(), None
    except Exception as e:
        return None, str(e)

def render_customize_resume_page():
    # Dynamic container sizing (wider for side-by-side layout)
    st.markdown(
        "<style>[data-testid='stAppViewBlockContainer'] { max-width: 1200px !important; margin: 1rem auto !important; }</style>",
        unsafe_allow_html=True
    )
    
    if st.session_state.get("job_desc_saved_toast"):
        st.toast("Job description updated! 📝")
        del st.session_state.job_desc_saved_toast
    if st.session_state.get("resume_tailored_toast"):
        st.toast("Resume tailored with AI! 🪄")
        del st.session_state.resume_tailored_toast

    job = st.session_state.get("customize_job")
    if not job:
        st.error("No job selected for customization.")
        if st.button("⬅ Back to Dashboard", type="secondary"):
            st.session_state.current_page = "dashboard"
            st.rerun()
        st.stop()
        
    # Re-fetch the latest job record from DB to ensure we have the description if it was saved before
    jobs_to_apply = db.get_jobs_to_apply()
    latest_job = next((j for j in jobs_to_apply if j["id"] == job["id"]), None)
    if latest_job:
        job = latest_job
        st.session_state.customize_job = latest_job


    is_desc_saved = bool(job.get("description") and job.get("description").strip())

    st.markdown('<div class="main-card" style="max-width: 100%; padding: 2rem;">', unsafe_allow_html=True)
    
    # Back to Dashboard button
    if st.button("⬅ Back to Dashboard", type="secondary"):
        st.session_state.current_page = "dashboard"
        st.rerun()
        
    st.markdown(f"<h2 style='color: #4A5D4E; margin-bottom: 0.2rem;'>🎯 Customize Resume for {job['role']}</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='color: #718096; font-size: 1rem;'>Company: <strong>{job['company']}</strong></p>", unsafe_allow_html=True)
    st.markdown("<hr style='border: 0; border-top: 1px solid #EFE8DD; margin: 1rem 0;'>", unsafe_allow_html=True)

    
    # Initialize and check API key
    if not os.getenv("OPENAI_API_KEY"):
        if "openai_api_key" in st.session_state:
            os.environ["OPENAI_API_KEY"] = st.session_state.openai_api_key
        else:
            st.warning("⚠️ OpenAI API Key is missing. Please add it to your `.env` file or enter it below to proceed:")
            key_input = st.text_input("OpenAI API Key", type="password", key="openai_key_input_tailor")
            if st.button("Save API Key 🔑", key="btn_save_key_tailor"):
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
        
    # Always initialize customized resume when entering the page
    if "custom_resume_initialized_job_id" not in st.session_state or st.session_state.custom_resume_initialized_job_id != job["id"]:
        st.session_state.custom_resume_initialized_job_id = job["id"]
        
        # Load the last tailored resume from database if it exists, otherwise fallback to default
        if job.get("tailored_resume") and job.get("tailored_resume").strip():
            st.session_state.custom_resume_text = job.get("tailored_resume")
        else:
            # Load the default version from database
            db_default = profile.get("default_resume")
            
            if not db_default:
                with st.spinner("Initializing your default resume..."):
                    if profile.get("resume_bytes"):
                        from career_assistant.ResumeBuilder import extract_all_text_from_pdf, generate_initial_markdown_from_text
                        raw_text = extract_all_text_from_pdf(profile["resume_bytes"])
                        if raw_text.strip():
                            db_default = generate_initial_markdown_from_text(
                                raw_text,
                                profile["full_name"],
                                profile["desired_role"],
                                profile["location"]
                            )
                    if not db_default or not db_default.strip():
                        from career_assistant.ResumeBuilder import generate_skeleton_markdown
                        db_default = generate_skeleton_markdown(
                            profile["full_name"],
                            profile["desired_role"],
                            profile["location"],
                            profile["skills"]
                        )
                    # Save to database's default columns so they are never overwritten
                    db.save_profile(
                        full_name=profile["full_name"],
                        desired_role=profile["desired_role"],
                        location=profile["location"],
                        resume_name=profile["resume_name"],
                        resume_bytes=profile["resume_bytes"],
                        skills=profile["skills"],
                        default_resume=db_default
                    )
            st.session_state.custom_resume_text = db_default
        
        # Delete any leftover text area widget state so Streamlit initializes it fresh with the new value
        if "resume_edit_textarea" in st.session_state:
            del st.session_state.resume_edit_textarea

    # Resolve job description: load from DB first, if not available, scrape URL.
    job_description = job.get("description")
    
    if not job_description or not job_description.strip():
        # Scrape description
        url = job.get("url", "")
        if url and url.strip().startswith("http"):
            with st.spinner("Extracting job description from URL..."):
                raw_text, err = extract_job_description_from_url(url)
                if err:
                    st.warning(f"Could not retrieve job description from URL automatically: {err}")
                    job_description = ""
                else:
                    # Optional AI format/summarization
                    job_description = format_job_description_with_ai(raw_text)
                    # Save to database so it doesn't scrape again next time
                    db.update_job_to_apply_description(job["id"], job_description)
                    st.success("Job description parsed and saved successfully!")
        else:
            job_description = ""

    # Side-by-side columns
    col_left, col_right = st.columns([5, 6])
    
    with col_left:
        st.markdown("### 📋 Job Description")
        if job.get("url"):
            st.markdown(f"[🔗 View Original Job Posting]({job['url']})", unsafe_allow_html=True)
            
        edited_desc = st.text_area(
            "Job Description (Markdown / Text)",
            value=job_description,
            height=500,
            key="job_desc_textarea",
            help="You can manually edit or paste the job description here."
        )
        
        if st.button("Save Job Description 💾", key="save_job_desc_btn", use_container_width=True):
            db.update_job_to_apply_description(job["id"], edited_desc)
            st.session_state.job_desc_saved_toast = True
            st.rerun()
            
    with col_right:
        st.markdown("### 📝 Edit Your Resume")
        st.markdown(f"Saved resume for **{profile['full_name']}**")
        
        if not is_desc_saved:
            st.info("⚠️ Please click 'Save Job Description 💾' on the left to save the description to the database before editing the resume.")
            
        edited_resume = st.text_area(
            "Resume Markdown Content",
            value=st.session_state.custom_resume_text,
            height=450,
            key="resume_edit_textarea",
            disabled=not is_desc_saved,
            help="Directly edit your resume markdown here. Make sure to save or download it."
        )
        
        with st.expander("👁️ Live Preview (with AI Highlights)", expanded=True):
            with st.container(border=True, height=450):
                # Render markdown with unsafe_allow_html=True to support `<mark>` styling
                st.markdown(st.session_state.custom_resume_text, unsafe_allow_html=True)
        
        if st.button("Tailor with AI 🪄", type="primary", use_container_width=True, key="tailor_custom_resume_btn", disabled=not is_desc_saved):
            # Load the latest job description directly from the database under jobs_to_apply
            latest_jobs = db.get_jobs_to_apply()
            current_job_db = next((j for j in latest_jobs if j["id"] == job["id"]), None)
            db_job_desc = current_job_db.get("description") if current_job_db else ""
            
            if not db_job_desc or not db_job_desc.strip():
                st.error("Please provide and save a job description first so the AI has context to tailor your resume.")
            else:
                with st.spinner("AI is tailoring your resume to the job description..."):
                    db_default = profile.get("default_resume") or ""
                    tailored, err = tailor_resume_with_ai(
                        resume_markdown=db_default,
                        job_description=db_job_desc,
                        target_role=job["role"],
                        company_name=job["company"]
                    )
                    if err:
                        st.error(err)
                    else:
                        db.update_job_to_apply_tailored_resume(job["id"], tailored)
                        st.session_state.custom_resume_text = tailored
                        if "resume_edit_textarea" in st.session_state:
                            del st.session_state.resume_edit_textarea
                        st.session_state.resume_tailored_toast = True
                        st.rerun()
                        
        st.markdown("<div style='margin-top: 0.5rem;'></div>", unsafe_allow_html=True)
        st.download_button(
            label="Download Resume 📥",
            data=strip_highlights(st.session_state.custom_resume_text),
            file_name=f"Resume_{profile['full_name'].replace(' ', '_')}_{job['company'].replace(' ', '_')}.md",
            mime="text/markdown",
            use_container_width=True,
            key="dl_custom_resume_btn"
        )
        
    st.markdown('</div>', unsafe_allow_html=True)
