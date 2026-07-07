import streamlit as st
import datetime
from career_assistant import db
from career_assistant import pdf_parser

# Helper function to render Stepper Progress
def render_stepper(current_step):
    steps = ["Name", "Role", "Location", "Resume", "Review"]
    cols = st.columns(len(steps))
    for idx, step_name in enumerate(steps):
        step_num = idx + 1
        with cols[idx]:
            if step_num < current_step:
                status = "completed"
                val = "✓"
            elif step_num == current_step:
                status = "active"
                val = str(step_num)
            else:
                status = "pending"
                val = str(step_num)
            
            st.markdown(
                f'<div class="step-container">'
                f'<div class="step-circle {status}">{val}</div>'
                f'<div class="step-label {status}">{step_name}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

def render_onboarding():
    # Page Header
    st.markdown(
        '<div class="onboarding-header">'
        '<h1 class="onboarding-title">Onboarding Journey</h1>'
        '<p class="onboarding-subtitle">Help us customize your career development assistant</p>'
        '</div>',
        unsafe_allow_html=True
    )

    # Render Stepper Progress
    render_stepper(st.session_state.step)
    st.markdown("<br><hr style='border: 0; border-top: 1px solid #EFE8DD; margin: 0 0 1.5rem 0;'><br>", unsafe_allow_html=True)

    # STEP 1: Name Input
    if st.session_state.step == 1:
        st.markdown("### Step 1: Tell us your name")
        st.markdown("Let's start by introducing yourself so we know who we are helping.")
        
        name_input = st.text_input(
            "Full Name", 
            value=st.session_state.full_name,
            placeholder="Jane Doe",
            help="Please enter your first and last name."
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col_prev, col_next = st.columns([1, 1])
        with col_prev:
            st.write("")  # Empty space since we can't go back
        with col_next:
            if st.button("Next ➔", type="primary", use_container_width=True):
                if name_input.strip() == "":
                    st.error("Name field is required.")
                else:
                    st.session_state.full_name = name_input.strip()
                    st.session_state.step = 2
                    st.rerun()

    # STEP 2: Desired Role Dropdown
    elif st.session_state.step == 2:
        st.markdown("### Step 2: Desired Career Path")
        st.markdown("Select the target role you want guidance for.")
        
        roles_list = [
            "Data Analyst",
            "Software Engineer",
            "Data Scientist",
            "Product Manager",
            "UX/UI Designer",
            "Financial Analyst",
            "Marketing Specialist",
            "Other"
        ]
        
        try:
            default_idx = roles_list.index(st.session_state.desired_role)
        except ValueError:
            default_idx = 0
            
        role_input = st.selectbox(
            "Desired Role",
            options=roles_list,
            index=default_idx,
            help="Select the role that best fits your career goals."
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col_prev, col_next = st.columns([1, 1])
        with col_prev:
            if st.button("⬅ Back", type="secondary", use_container_width=True):
                st.session_state.desired_role = role_input
                st.session_state.step = 1
                st.rerun()
        with col_next:
            if st.button("Next ➔", type="primary", use_container_width=True):
                st.session_state.desired_role = role_input
                st.session_state.step = 3
                st.rerun()

    # STEP 3: Location Preferences (Choose up to 3 US Locations)
    elif st.session_state.step == 3:
        st.markdown("### Step 3: Location Preferences")
        st.markdown("Select up to 3 work locations within the United States (including 'Remote').")
        
        # Initialize location options list in state
        if "location_options" not in st.session_state:
            st.session_state.location_options = [
                "Remote", "New York, NY", "San Francisco, CA", "Seattle, WA", "Austin, TX",
                "Boston, MA", "Chicago, IL", "Los Angeles, CA", "Denver, CO", "Atlanta, GA",
                "Washington, DC", "Miami, FL", "Dallas, TX"
            ]
            
        # Parse loaded values
        default_selected = []
        if st.session_state.location:
            default_selected = [loc.strip() for loc in st.session_state.location.split("; ") if loc.strip()]
        else:
            default_selected = ["Remote"]
            
        # Make sure selected values are in the options list
        for loc in default_selected:
            if loc not in st.session_state.location_options:
                st.session_state.location_options.append(loc)
                
        col_multi, col_add = st.columns([3, 2])
        with col_multi:
            selected_locations = st.multiselect(
                "Work Locations (Select up to 3)",
                options=st.session_state.location_options,
                default=default_selected,
                max_selections=3,
                help="Choose up to 3 work locations within the United States. You can include 'Remote'."
            )
        with col_add:
            new_loc = st.text_input("Add Custom US Location", placeholder="e.g. San Diego, CA")
            if st.button("Add Location ➕", use_container_width=True):
                new_loc_clean = new_loc.strip()
                if new_loc_clean:
                    if new_loc_clean not in st.session_state.location_options:
                        st.session_state.location_options.append(new_loc_clean)
                    if len(selected_locations) < 3 and new_loc_clean not in selected_locations:
                        selected_locations.append(new_loc_clean)
                    st.session_state.location = "; ".join(selected_locations)
                    st.rerun()
                    
        st.markdown("<br>", unsafe_allow_html=True)
        
        col_prev, col_next = st.columns([1, 1])
        with col_prev:
            if st.button("⬅ Back", type="secondary", use_container_width=True):
                st.session_state.location = "; ".join(selected_locations)
                st.session_state.step = 2
                st.rerun()
        with col_next:
            if st.button("Next ➔", type="primary", use_container_width=True):
                if not selected_locations:
                    st.error("Please select at least one location preference.")
                else:
                    st.session_state.location = "; ".join(selected_locations)
                    st.session_state.step = 4
                    st.rerun()

    # STEP 4: Resume PDF File Uploader
    elif st.session_state.step == 4:
        st.markdown("### Step 4: Upload Resume")
        st.markdown("Upload your resume in PDF format so we can inspect your credentials.")
        
        if st.session_state.resume_file:
            st.info(f"📄 Currently selected: {st.session_state.resume_file['name']} ({st.session_state.resume_file['size_str']})")
            
        uploaded_file = st.file_uploader(
            "Upload Resume (PDF only)",
            type=["pdf"],
            help="Upload a PDF file (Max 200MB)."
        )
        
        if uploaded_file is not None:
            size_bytes = uploaded_file.size
            if size_bytes < 1024 * 1024:
                size_str = f"{size_bytes / 1024:.1f} KB"
            else:
                size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
                
            st.session_state.resume_file = {
                "name": uploaded_file.name,
                "size_str": size_str,
                "bytes": uploaded_file.getvalue()
            }
            st.success(f"Successfully uploaded: {uploaded_file.name}")
        else:
            st.markdown("<div style='text-align: center; margin: 0.5rem 0; color: #718096;'>— OR —</div>", unsafe_allow_html=True)
            if st.button("Use Sample Resume (Testing)", type="secondary", use_container_width=True):
                try:
                    sample_path = "/Users/annix/.gemini/antigravity-ide/brain/fb28a69a-d414-4d3e-a240-77bdb7bfbed4/scratch/dummy_resume.pdf"
                    with open(sample_path, "rb") as sample_f:
                        pdf_data = sample_f.read()
                except Exception as e:
                    pdf_data = b"%PDF-1.4 mock resume data containing Python, SQL, React, AWS, Docker"
                st.session_state.resume_file = {
                    "name": "dummy_resume.pdf",
                    "size_str": f"{len(pdf_data)/1024:.1f} KB",
                    "bytes": pdf_data
                }
                st.success("Sample resume loaded successfully!")
                st.rerun()
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        col_prev, col_next = st.columns([1, 1])
        with col_prev:
            if st.button("⬅ Back", type="secondary", use_container_width=True):
                st.session_state.step = 3
                st.rerun()
        with col_next:
            if st.button("Next ➔", type="primary", use_container_width=True):
                if not st.session_state.resume_file:
                    st.error("Please upload a resume file to proceed.")
                else:
                    st.session_state.skills = pdf_parser.extract_skills_from_pdf(st.session_state.resume_file["bytes"])
                    st.session_state.step = 5
                    st.rerun()

    # STEP 5: Summary Screen
    elif st.session_state.step == 5:
        st.markdown("### 🎉 Profile Created!")
        st.markdown("All details have been submitted. Let's review your onboarding profile.")
        
        resume_name = st.session_state.resume_file["name"] if st.session_state.resume_file else "N/A"
        resume_size = st.session_state.resume_file["size_str"] if st.session_state.resume_file else "N/A"
        
        st.markdown(
            f"""
            <div class="summary-card">
                <div class="summary-item">
                    <div class="summary-label">Full Name</div>
                    <div class="summary-value">{st.session_state.full_name}</div>
                </div>
                <div class="summary-item">
                    <div class="summary-label">Desired Role</div>
                    <div class="summary-value">{st.session_state.desired_role}</div>
                </div>
                <div class="summary-item">
                    <div class="summary-label">Preferred Location(s)</div>
                    <div class="summary-value">{st.session_state.location.replace("; ", " | ") if st.session_state.location else "Remote"}</div>
                </div>
                <div class="summary-item">
                    <div class="summary-label">Uploaded Resume</div>
                    <div class="summary-value">📄 {resume_name} ({resume_size})</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col_reset, col_dashboard = st.columns([1, 1])
        with col_reset:
            if st.button("Restart Onboarding", type="secondary", use_container_width=True):
                db.clear_profile()
                st.session_state.step = 1
                st.session_state.full_name = ""
                st.session_state.desired_role = "Data Analyst"
                st.session_state.location = ""
                st.session_state.resume_file = None
                st.rerun()
        with col_dashboard:
            if st.button("Go to Dashboard ➔", type="primary", use_container_width=True):
                # Persist the profile info to database
                resume_name = st.session_state.resume_file["name"] if st.session_state.resume_file else None
                resume_bytes = st.session_state.resume_file["bytes"] if st.session_state.resume_file else None
                db.save_profile(
                    full_name=st.session_state.full_name,
                    desired_role=st.session_state.desired_role,
                    location=st.session_state.location,
                    resume_name=resume_name,
                    resume_bytes=resume_bytes,
                    skills=st.session_state.skills
                )
                st.session_state.onboarded = True
                st.rerun()
