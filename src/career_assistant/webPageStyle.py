# Custom Premium Styling for Sage Green & Soft Cream theme
custom_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Viewport background and typography setup */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #FAF6F0 !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Center the main container and make it look like an elegant card */
    [data-testid="stAppViewBlockContainer"] {
        background-color: #FFFFFF !important;
        border-radius: 16px;
        padding: 3rem 2.5rem !important;
        box-shadow: 0 10px 30px rgba(74, 93, 78, 0.05);
        border: 1px solid #EFE8DD;
        max-width: 580px !important; /* Overridden to 900px on Dashboard */
        margin: 4rem auto !important;
    }
    
    /* Hide Streamlit brandings for clean appearance */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Premium Header */
    .onboarding-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    .onboarding-title {
        color: #2B2D2F;
        font-weight: 700;
        font-size: 1.85rem;
        margin-bottom: 0.5rem;
        letter-spacing: -0.025em;
    }
    .onboarding-subtitle {
        color: #6D7275;
        font-size: 0.95rem;
        font-weight: 400;
    }
    
    /* Stepper Styling */
    .step-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
    }
    .step-circle {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        font-size: 0.85rem;
        margin-bottom: 0.4rem;
        transition: all 0.3s ease;
    }
    .step-circle.completed {
        background-color: #E8EFE9;
        color: #4A5D4E;
        border: 2px solid #4A5D4E;
    }
    .step-circle.active {
        background-color: #4A5D4E;
        color: #FFFFFF;
        border: 2px solid #4A5D4E;
        box-shadow: 0 0 12px rgba(74, 93, 78, 0.25);
    }
    .step-circle.pending {
        background-color: #FFFFFF;
        color: #A0AEC0;
        border: 2px solid #E2E8F0;
    }
    .step-label {
        font-size: 0.72rem;
        font-weight: 500;
        color: #718096;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .step-label.active {
        color: #2D3748;
        font-weight: 600;
    }
    .step-label.completed {
        color: #4A5D4E;
    }
    
    /* Form fields and selectors styling */
    div[data-baseweb="input"], div[data-baseweb="select"] {
        border-radius: 8px !important;
        border-color: #E2E8F0 !important;
        background-color: #FDFBF9 !important;
    }
    
    /* Premium file uploader container */
    [data-testid="stFileUploader"] {
        border: 1px dashed #D0C6B8 !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
        background-color: #FDFBF9 !important;
    }
    
    /* Standardized premium button style */
    div.stButton > button {
        border-radius: 8px !important;
        padding: 0.6rem 1rem !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        width: 100%;
        display: flex;
        justify-content: center;
        align-items: center;
        border: 1px solid #4A5D4E !important;
        white-space: nowrap !important;
    }

    /* Primary Button Style */
    div.stButton > button[data-testid="baseButton-primary"] {
        background-color: #4A5D4E !important;
        color: #FFFFFF !important;
    }
    div.stButton > button[data-testid="baseButton-primary"]:hover {
        background-color: #3B4B3F !important;
        border-color: #3B4B3F !important;
        box-shadow: 0 4px 12px rgba(74, 93, 78, 0.15) !important;
    }

    /* Secondary Button Style */
    div.stButton > button[data-testid="baseButton-secondary"] {
        background-color: transparent !important;
        color: #4A5D4E !important;
    }
    div.stButton > button[data-testid="baseButton-secondary"]:hover {
        background-color: #EBF2EC !important;
    }

    /* Style for warning/error messages */
    .stAlert {
        border-radius: 8px !important;
    }
    
    /* Summary and Dashboard Cards styling */
    .summary-card, .dashboard-card {
        background-color: #FAF8F5;
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #EFE8DD;
        margin-top: 1rem;
        margin-bottom: 2rem;
    }
    .summary-item {
        margin-bottom: 1rem;
    }
    .summary-item:last-child {
        margin-bottom: 0;
    }
    .summary-label {
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        color: #7A8288;
        letter-spacing: 0.05em;
    }
    .summary-value {
        font-size: 1.05rem;
        font-weight: 500;
        color: #2B2D2F;
        margin-top: 0.2rem;
    }

    /* Dashboard Header CSS */
    .dashboard-welcome {
        color: #2B2D2F;
        font-weight: 700;
        font-size: 1.95rem;
        letter-spacing: -0.025em;
        margin-bottom: 0.2rem;
    }
    .dashboard-meta {
        font-size: 0.95rem;
        color: #6D7275;
        margin-bottom: 1.5rem;
    }

    /* Tracker Job Cards */
    .job-card {
        background-color: #FAF8F5;
        border-radius: 10px;
        padding: 1.1rem;
        border: 1px solid #EFE8DD;
        margin-bottom: 0.5rem;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .job-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(74, 93, 78, 0.04);
    }
    .job-company {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        color: #4A5D4E;
        letter-spacing: 0.05em;
        margin-bottom: 0.25rem;
    }
    .job-title {
        font-size: 1rem;
        font-weight: 600;
        color: #2B2D2F;
        margin-bottom: 0.35rem;
    }
    .job-meta {
        font-size: 0.82rem;
        color: #718096;
    }

    /* Action Result Cards */
    .action-result-card {
        background-color: #FAF6F0;
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #EFE8DD;
        margin-top: 1.5rem;
        animation: fadeIn 0.3s ease-out;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .insight-stat-box {
        background-color: #FFFFFF;
        border-radius: 8px;
        padding: 0.85rem;
        text-align: center;
        border: 1px solid #EFE8DD;
    }
    .insight-stat-value {
        font-size: 1.45rem;
        font-weight: 700;
        color: #4A5D4E;
    }
    .insight-stat-label {
        font-size: 0.72rem;
        text-transform: uppercase;
        color: #718096;
        letter-spacing: 0.04em;
        margin-top: 0.15rem;
    }
    
    /* Mobile responsive tweaks */
    @media (max-width: 640px) {
        [data-testid="stAppViewBlockContainer"] {
            padding: 2rem 1.5rem !important;
            margin: 1.5rem auto !important;
            border-radius: 12px;
        }
        .onboarding-title {
            font-size: 1.5rem;
        }
    }
    
    /* Profile Summary Section Styling */
    .profile-summary-card {
        background-color: #FFFFFF;
        border: 1px solid #EFE8DD;
        border-radius: 10px;
        padding: 0.6rem 0.9rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.01);
        margin-top: 0.1rem;
        margin-bottom: 0.8rem;
    }
    .skill-tag {
        background-color: #F0F4F1;
        color: #4A5D4E;
        padding: 0.15rem 0.45rem;
        border-radius: 20px;
        font-size: 0.76rem;
        font-weight: 500;
        border: 1px solid #E2EAE4;
        display: inline-block;
    }
    
    /* Custom Styling for chat message Delete Buttons */
    div[class*="st-key-del_msg_"] button,
    div[class*="st-key-del_res_msg_"] button {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        width: auto !important;
        min-width: 0 !important;
        height: auto !important;
        font-size: 1.1rem !important;
        color: #A0AEC0 !important;
        margin: 0 !important;
    }
    div[class*="st-key-del_msg_"] button:hover,
    div[class*="st-key-del_res_msg_"] button:hover {
        background-color: transparent !important;
        color: #E53E3E !important;
        border: none !important;
        box-shadow: none !important;
    }
    
    /* Shrink the planned jobs tracker buttons */
    div[class*="st-key-move_to_applied_"] button,
    div[class*="st-key-apply_job_"] button,
    div[class*="st-key-del_to_apply_"] button {
        padding: 0.35rem 0.5rem !important;
        font-size: 0.76rem !important;
        height: auto !important;
        min-height: 0 !important;
        white-space: nowrap !important;
    }
    
    /* Custom styling for history page delete buttons */
    div[class*="st-key-del_hist_"] button {
        padding: 0.3rem 0.6rem !important;
        font-size: 0.85rem !important;
        height: auto !important;
        min-height: 0 !important;
        background-color: #FAF2F2 !important;
        color: #C53030 !important;
        border: 1px solid #FEB2B2 !important;
        border-radius: 6px !important;
        transition: all 0.2s ease !important;
    }
    div[class*="st-key-del_hist_"] button:hover {
        background-color: #E53E3E !important;
        color: #FFFFFF !important;
        border-color: #E53E3E !important;
    }
</style>
"""
