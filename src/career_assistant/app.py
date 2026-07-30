import streamlit as st
import datetime
from career_assistant import db

# Initialize SQLite database
db.init_db()

# Page configuration (default centered layout)
st.set_page_config(
    page_title="Career Assistant | Portal",
    page_icon="💼",
    layout="centered",
    initial_sidebar_state="collapsed",
)

def render_full_list_page():
    st.markdown('<div class="main-card" style="max-width: 900px; margin: 0 auto; padding: 2rem;">', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: #4A5D4E; margin-bottom: 0.5rem;'>📋 Full Applied Jobs History</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #718096; font-size: 0.9rem;'>All applications tracked in your database.</p>", unsafe_allow_html=True)
    
    # Back to Dashboard button
    if st.button("⬅ Back to Dashboard", type="secondary", use_container_width=True):
        st.session_state.current_page = "dashboard"
        st.rerun()
        
    st.markdown("<hr style='border: 0; border-top: 1px solid #EFE8DD; margin: 1.5rem 0;'>", unsafe_allow_html=True)
    
    jobs = db.get_jobs_applied()
    if not jobs:
        st.info("No applied jobs found in the history.")
    else:
        # Render beautiful grid-based list with delete buttons
        header_cols = st.columns([0.6, 1.8, 2.2, 1.8, 2.0, 2.0, 0.8])
        with header_cols[0]:
            st.markdown("**#**")
        with header_cols[1]:
            st.markdown("**Company**")
        with header_cols[2]:
            st.markdown("**Role Title**")
        with header_cols[3]:
            st.markdown("**Date Applied**")
        with header_cols[4]:
            st.markdown("**Job Link**")
        with header_cols[5]:
            st.markdown("**Status**")
        with header_cols[6]:
            st.markdown("**Action**")
            
        st.markdown("<hr style='border: 0; border-top: 2px solid #4A5D4E; margin: 0.5rem 0;'>", unsafe_allow_html=True)
        
        for idx, job in enumerate(jobs):
            row_cols = st.columns([0.6, 1.8, 2.2, 1.8, 2.0, 2.0, 0.8])
            with row_cols[0]:
                st.write(f"{idx + 1}")
            with row_cols[1]:
                st.write(job["company"])
            with row_cols[2]:
                st.write(job["role"])
            with row_cols[3]:
                st.write(job["date"])
            with row_cols[4]:
                if job["url"]:
                    st.markdown(f'[🔗 Link]({job["url"]})')
                else:
                    st.markdown("<span style='color: #A0AEC0;'>None</span>", unsafe_allow_html=True)
            with row_cols[5]:
                status_options = ["Applied", "Interviewed"]
                current_status = job.get("status") or "Applied"
                try:
                    default_idx = status_options.index(current_status)
                except ValueError:
                    default_idx = 0
                selected_status = st.selectbox(
                    "Status",
                    options=status_options,
                    index=default_idx,
                    key=f"status_hist_{job['id']}",
                    label_visibility="collapsed"
                )
                if selected_status != current_status:
                    db.update_job_status(job['id'], selected_status)
                    st.rerun()
            with row_cols[6]:
                if st.button("🗑️", key=f"del_hist_{job['id']}", help="Delete from history"):
                    db.delete_job_applied(job['id'])
                    st.rerun()
            st.markdown("<hr style='border: 0; border-top: 1px solid #EFE8DD; margin: 0.25rem 0;'>", unsafe_allow_html=True)
            
    st.markdown('</div>', unsafe_allow_html=True)

# Initialize Session State
if "onboarded" not in st.session_state:
    st.session_state.onboarded = False
if "step" not in st.session_state:
    st.session_state.step = 1
if "full_name" not in st.session_state:
    st.session_state.full_name = ""
if "desired_role" not in st.session_state:
    st.session_state.desired_role = "Data Analyst"
if "location" not in st.session_state:
    st.session_state.location = ""
if "skills" not in st.session_state:
    st.session_state.skills = ""
if "resume_file" not in st.session_state:
    st.session_state.resume_file = None
if "show_recommendations" not in st.session_state:
    st.session_state.show_recommendations = False
if "show_market_insights" not in st.session_state:
    st.session_state.show_market_insights = False
if "current_page" not in st.session_state:
    st.session_state.current_page = "dashboard"

# Load profile from SQLite database on application load
if "db_profile_loaded" not in st.session_state:
    profile = db.get_profile()
    if profile:
        st.session_state.onboarded = True
        st.session_state.full_name = profile["full_name"]
        st.session_state.desired_role = profile["desired_role"]
        st.session_state.location = profile["location"]
        
        # Load or parse skills
        skills = profile.get("skills")
        if not skills and profile["resume_bytes"]:
            from career_assistant import pdf_parser
            skills = pdf_parser.extract_skills_from_pdf(profile["resume_bytes"])
            # Save it back to update the database
            db.save_profile(
                full_name=profile["full_name"],
                desired_role=profile["desired_role"],
                location=profile["location"],
                resume_name=profile["resume_name"],
                resume_bytes=profile["resume_bytes"],
                skills=skills
            )
        st.session_state.skills = skills or ""
        
        if profile["resume_name"]:
            st.session_state.resume_file = {
                "name": profile["resume_name"],
                "size_str": "Uploaded",
                "bytes": profile["resume_bytes"]
            }
    st.session_state.db_profile_loaded = True

# Custom Premium Styling for Sage Green & Soft Cream theme
from career_assistant.webPageStyle import custom_css
st.markdown(custom_css, unsafe_allow_html=True)

# Conditional Dynamic Container Sizing
if st.session_state.onboarded:
    st.markdown(
        "<style>[data-testid='stAppViewBlockContainer'] { max-width: 900px !important; margin: 2rem auto !important; }</style>",
        unsafe_allow_html=True
    )

# VIEW: ONBOARDING FLOW
if not st.session_state.onboarded:
    from career_assistant import onboarding
    onboarding.render_onboarding()

# ==========================================
# VIEW: USER DASHBOARD
# ==========================================
else:
    if st.session_state.get("current_page", "dashboard") == "full_list":
        render_full_list_page()
        st.stop()

    if st.session_state.get("current_page", "dashboard") == "customize_resume":
        from career_assistant import customResumeBuilder
        import importlib
        importlib.reload(customResumeBuilder)
        customResumeBuilder.render_customize_resume_page()
        st.stop()

    # Extract first name
    first_name = st.session_state.full_name.split()[0] if st.session_state.full_name else "User"
    desired_role = st.session_state.desired_role
    location = st.session_state.location
    resume_name = st.session_state.resume_file["name"] if st.session_state.resume_file else "N/A"
    loc_display = location.replace("; ", " | ") if location else "Remote"

    # Header section
    col_header, col_reset_btn = st.columns([3, 1])
    with col_header:
        st.markdown(f'<div class="dashboard-welcome">Welcome back, {first_name}! 👋</div>', unsafe_allow_html=True)
    with col_reset_btn:
        st.markdown("<div style='margin-top: 0.5rem;'></div>", unsafe_allow_html=True)
        if st.button("Reset Profile", type="secondary", use_container_width=True):
            db.clear_profile()
            st.session_state.onboarded = False
            st.session_state.step = 1 # Return to step 1
            st.session_state.full_name = ""
            st.session_state.desired_role = "Data Analyst"
            st.session_state.location = ""
            st.session_state.resume_file = None
            st.session_state.show_recommendations = False
            st.session_state.show_market_insights = False
            st.rerun()

    st.markdown("<hr style='border: 0; border-top: 1px solid #EFE8DD; margin: 0 0 1.5rem 0;'>", unsafe_allow_html=True)

    # Profile Summary & Skills Section (just below welcome banner)
    skills_list = [s.strip() for s in st.session_state.get("skills", "").split(",") if s.strip()]
    if skills_list:
        skills_html = "".join([f'<span class="skill-tag">{skill}</span>' for skill in skills_list])
    else:
        skills_html = '<span style="color: #6C757D; font-style: italic;">No skills detected. Upload a resume to extract skills.</span>'
        
    st.markdown(
        f"""
        <div class="profile-summary-card">
            <div style="display: flex; flex-wrap: wrap; gap: 1.2rem; align-items: center; margin-bottom: 0.5rem; font-size: 0.88rem; color: #2E332E;">
                <div>🎯 Role: <strong>{desired_role}</strong></div>
                <div style="color: #EFE8DD;">|</div>
                <div>📍 Locations: <strong>{loc_display}</strong></div>
                <div style="color: #EFE8DD;">|</div>
                <div>📄 Resume: <strong>{resume_name}</strong></div>
            </div>
            <div style="border-top: 1px dashed #EFE8DD; padding-top: 0.5rem; display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;">
                <span style="font-size: 0.78rem; color: #7D847B; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-right: 0.2rem;">Extracted Skills:</span>
                <div style="display: flex; flex-wrap: wrap; gap: 0.35rem; align-items: center;">
                    {skills_html}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Fetch trackers from SQLite database
    jobs_applied = db.get_jobs_applied()
    jobs_to_apply = db.get_jobs_to_apply()

    # Job trackers (Applied vs. To Apply)
    col_applied, col_to_apply = st.columns([1, 1])

    # Left Column: Jobs Applied
    with col_applied:
        st.markdown("### 📥 Jobs Applied")
        st.markdown("Track the status of applications you have submitted.")
        
        if st.button("View Full List 📋", key="btn_view_full_list", type="primary", use_container_width=True):
            st.session_state.current_page = "full_list"
            st.rerun()
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        if not jobs_applied:
            st.info("No applications logged yet.")
        else:
            for idx, job in enumerate(jobs_applied):
                status_val = job.get('status') or 'Applied'
                with st.expander(f"💼 {job['role']}, {job['company']} ({status_val})"):
                    edited_company = st.text_input("Company", value=job['company'], key=f"edit_company_{job['id']}")
                    edited_role = st.text_input("Role Title", value=job['role'], key=f"edit_role_{job['id']}")
                    edited_url = st.text_input("Job URL", value=job.get('url', ''), key=f"edit_url_{job['id']}", placeholder="https://example.com/job")
                    
                    try:
                        date_val = datetime.datetime.strptime(job['date'], "%Y-%m-%d").date()
                    except:
                        date_val = datetime.date.today()
                    edited_date = st.date_input("Date Applied", value=date_val, key=f"edit_date_{job['id']}")
                    
                    status_options = ["Applied", "Interviewed"]
                    try:
                        default_idx = status_options.index(status_val)
                    except ValueError:
                        default_idx = 0
                    edited_status = st.selectbox(
                        "Status",
                        options=status_options,
                        index=default_idx,
                        key=f"edit_status_{job['id']}"
                    )
                    
                    col_btn_save, col_btn_del = st.columns([3, 2])
                    with col_btn_save:
                        if st.button("Save 💾", key=f"save_applied_{job['id']}", type="primary", use_container_width=True):
                            if edited_company.strip() == "" or edited_role.strip() == "":
                                st.error("Company and Role are required.")
                            else:
                                db.update_job_applied(
                                    job_id=job['id'],
                                    company=edited_company.strip(),
                                    role=edited_role.strip(),
                                    date=edited_date.strftime("%Y-%m-%d"),
                                    url=edited_url.strip(),
                                    status=edited_status
                                )
                                st.rerun()
                    with col_btn_del:
                        if st.button("Delete", key=f"del_applied_{job['id']}", type="secondary", use_container_width=True):
                            db.delete_job_applied(job['id'])
                            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        # Form to add job to Applied
        with st.expander("➕ Log Applied Job"):
            with st.form("add_applied_form", clear_on_submit=True):
                new_company = st.text_input("Company Name", key="new_app_company")
                new_role = st.text_input("Role Title", value=desired_role, key="new_app_role")
                new_url = st.text_input("Job URL (Optional)", key="new_app_url", placeholder="https://example.com/job")
                new_date = st.date_input("Date Applied", value=datetime.date.today(), key="new_app_date")
                new_status = st.selectbox("Status", options=["Applied", "Interviewed"], index=0, key="new_app_status")
                
                submitted = st.form_submit_button("Log Application", type="primary", use_container_width=True)
                if submitted:
                    if new_company.strip() == "" or new_role.strip() == "":
                        st.error("Company and Role are required.")
                    else:
                        db.add_job_applied(
                            company=new_company.strip(),
                            role=new_role.strip(),
                            date=new_date.strftime("%Y-%m-%d"),
                            url=new_url.strip() if new_url.strip() else "",
                            status=new_status
                        )
                        st.success("Application logged!")
                        st.rerun()

    # Right Column: Jobs To Apply
    with col_to_apply:
        st.markdown("### 📋 Jobs To Apply")
        st.markdown("Keep track of roles you are planning to target.")
        
        if not jobs_to_apply:
            st.info("No planned jobs logged yet.")
        else:
            for idx, job in enumerate(jobs_to_apply):
                url_section = f'<div class="job-meta" style="margin-top: 0.25rem;"><a href="{job["url"]}" target="_blank" style="color: #4A5D4E; text-decoration: none; font-weight: 600; font-size: 0.82rem;">🔗 View Job Posting</a></div>' if job.get('url') else ""
                st.markdown(
                    f"""
                    <div class="job-card" style="margin-bottom: 0.35rem;">
                        <div class="job-company">{job['company']}</div>
                        <div class="job-title">{job['role']}</div>
                        {url_section}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                col_btn_move, col_btn_apply, col_btn_del = st.columns([1.3, 1.0, 0.9])
                with col_btn_move:
                    if st.button("Move to applied", key=f"move_to_applied_{job['id']}", type="primary", use_container_width=True):
                        today_str = datetime.date.today().strftime("%Y-%m-%d")
                        db.move_to_applied(job['id'], today_str)
                        st.rerun()
                with col_btn_apply:
                    if st.button("Apply", key=f"apply_job_{job['id']}", type="primary", use_container_width=True):
                        st.session_state.current_page = "customize_resume"
                        st.session_state.customize_job = job
                        if "custom_resume_initialized_job_id" in st.session_state:
                            del st.session_state.custom_resume_initialized_job_id
                        st.rerun()
                with col_btn_del:
                    if st.button("Delete", key=f"del_to_apply_{job['id']}", type="secondary", use_container_width=True):
                        db.delete_job_to_apply(job['id'])
                        st.rerun()
                st.markdown("<div style='margin-bottom: 0.8rem;'></div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        # Form to add job to To Apply
        with st.expander("➕ Plan New Application"):
            with st.form("add_to_apply_form", clear_on_submit=True):
                new_company = st.text_input("Company Name", key="new_plan_company")
                new_role = st.text_input("Role Title", value=desired_role, key="new_plan_role")
                new_url = st.text_input("Job URL (Optional)", key="new_plan_url", placeholder="https://example.com/job")
                
                submitted = st.form_submit_button("Plan Application", type="primary", use_container_width=True)
                if submitted:
                    if new_company.strip() == "" or new_role.strip() == "":
                        st.error("Company and Role are required.")
                    else:
                        db.add_job_to_apply(
                            company=new_company.strip(),
                            role=new_role.strip(),
                            url=new_url.strip() if new_url.strip() else ""
                        )
                        st.success("Job planned successfully!")
                        st.rerun()

    st.markdown("<br><hr style='border: 0; border-top: 1px solid #EFE8DD; margin: 1.5rem 0;'><br>", unsafe_allow_html=True)

    # Render the interactive Job Search and Resume Builder Chatboxes
    chat_tab1, chat_tab2 = st.tabs(["💬 Job Search Assistant", "📝 Resume Builder Agent"])
    
    with chat_tab1:
        from career_assistant import chatbox
        chatbox.render_chatbox()
        
    with chat_tab2:
        from career_assistant import ResumeBuilder
        ResumeBuilder.render_resume_builder()

    st.markdown("<br><hr style='border: 0; border-top: 1px solid #EFE8DD; margin: 1.5rem 0;'><br>", unsafe_allow_html=True)

    # Actions panel (Bottom Section)
    st.markdown("### 📊 AI Insights & Market Analysis")
    st.markdown("Leverage AI to fetch recommendations or analyze your local target market.")
    
    col_action1, col_action2 = st.columns([1, 1])
    with col_action1:
        if st.button("Get Job Recommendations 🔍", type="primary", use_container_width=True):
            st.session_state.show_recommendations = True
            st.session_state.show_market_insights = False
            st.rerun()
    with col_action2:
        if st.button("Analyze Job Market 📈", type="primary", use_container_width=True):
            st.session_state.show_market_insights = True
            st.session_state.show_recommendations = False
            st.rerun()

    # Recommendations Result Box
    if st.session_state.show_recommendations:
        st.markdown('<div class="action-result-card">', unsafe_allow_html=True)
        st.markdown(f"#### 🔍 Recommended Roles for target: **{desired_role}** ({location})")
        st.markdown("Based on your uploaded resume and career target, we recommend the following openings:")
        
        # Recommendations Mock Data
        recs = [
            {"company": "Stripe", "role": f"Lead {desired_role}", "salary": "$125,000 - $160,000 / yr", "desc": "Lead our growth analytics team focusing on payment volumes and churn modeling."},
            {"company": "Airbnb", "role": f"Senior {desired_role}", "salary": "$135,000 - $170,000 / yr", "desc": "Join our marketplace operations team to design data frameworks and key business metrics."},
            {"company": "Slack", "role": f"Staff Product {desired_role}", "salary": "$140,000 - $185,000 / yr", "desc": "Own analytics strategy for the core user messaging experience. Remote eligible."}
        ]
        
        for rec in recs:
            st.markdown(
                f"""
                <div class="job-card" style="background-color: #FFFFFF; margin-bottom: 0.8rem;">
                    <div class="job-company">{rec['company']} &nbsp;|&nbsp; 💰 {rec['salary']}</div>
                    <div class="job-title" style="color: #4A5D4E;">{rec['role']}</div>
                    <div class="job-meta" style="color: #4A5D4E; font-weight: 500;">Location: {location} (Remote friendly)</div>
                    <p style="font-size: 0.85rem; color: #555; margin: 0.4rem 0 0 0;">{rec['desc']}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        st.markdown('</div>', unsafe_allow_html=True)

    # Market Analysis Result Box
    if st.session_state.show_market_insights:
        st.markdown('<div class="action-result-card">', unsafe_allow_html=True)
        st.markdown(f"#### 📈 Job Market Insights: **{desired_role}** in **{location}**")
        st.markdown(f"Real-time hiring trends and target statistics for {desired_role} roles:")
        
        # 3 Grid statistics cards
        col_stat1, col_stat2, col_stat3 = st.columns([1, 1, 1])
        with col_stat1:
            st.markdown(
                """
                <div class="insight-stat-box">
                    <div class="insight-stat-value">$118,500</div>
                    <div class="insight-stat-label">Median Salary</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col_stat2:
            st.markdown(
                f"""
                <div class="insight-stat-box">
                    <div class="insight-stat-value">1,450+</div>
                    <div class="insight-stat-label">Active Openings ({location})</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col_stat3:
            st.markdown(
                """
                <div class="insight-stat-box">
                    <div class="insight-stat-value" style="color: #C05621;">High 🔥</div>
                    <div class="insight-stat-label">Market Demand</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
        # Skill insights based on role
        if "software" in desired_role.lower():
            skills = "Python/JavaScript, React/Vue, System Design, SQL, Git, AWS/GCP, Docker"
            top_employers = "Google, Apple, Salesforce, Amazon, Snowflake"
        elif "analyst" in desired_role.lower():
            skills = "SQL, Python/R, Tableau/PowerBI, A/B Testing, Excel, Statistics, Product Analytics"
            top_employers = "Meta, Netflix, Uber, Stripe, Capital One"
        elif "designer" in desired_role.lower():
            skills = "Figma, Wireframing, User Testing, Prototyping, Design Systems, Typography, HTML/CSS"
            top_employers = "Figma, Airbnb, Pinterest, Canva, Adobe"
        elif "product" in desired_role.lower():
            skills = "Product Strategy, Roadmap Design, Agile/Scrum, User Research, Jira, Data-driven Decision Making"
            top_employers = "Atlassian, Microsoft, Google, HubSpot, Spotify"
        else:
            skills = "Project Management, Communication, Data Analysis, CRM Toolsets, Strategic Planning"
            top_employers = "Consulting Firms, High-growth Tech Scaleups, Financial Institutions"

        st.markdown(
            f"""
            <div style="margin-top: 1rem;">
                <p><strong>🔥 Top In-Demand Skills:</strong> <span style="color: #4A5D4E; font-weight: 500;">{skills}</span></p>
                <p><strong>🏢 Top Hiring Companies:</strong> {top_employers}</p>
                <p><strong>📈 Quarter-over-Quarter Trend:</strong> Hiring in this sector has seen a <strong>+14% QoQ</strong> increase. Remote flexibility continues to be offered in roughly 45% of postings.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown('</div>', unsafe_allow_html=True)
