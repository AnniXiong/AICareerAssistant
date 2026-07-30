import io
import re
import logging
import pypdf

# Suppress pypdf warning logs (e.g., incorrect startxref pointer)
logging.getLogger("pypdf").setLevel(logging.ERROR)


def extract_skills_from_pdf(pdf_bytes):
    if not pdf_bytes:
        return ""
        
    try:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""
        
    # Standard list of skills to search for (case-insensitive)
    SKILLS_DATABASE = [
        # Programming Languages
        "Python", "JavaScript", "TypeScript", "Java", "C\\+\\+", "C#", "Golang", "Go", "Rust", "Ruby", "Swift", "Kotlin", "PHP", 
        "HTML", "CSS", "SQL", "NoSQL",
        # Frameworks & Web Development
        "React", "Angular", "Vue", "Node\\.js", "Node", "Django", "Flask", "FastAPI", "Spring Boot", "Express",
        # Data & Artificial Intelligence
        "Pandas", "NumPy", "TensorFlow", "PyTorch", "Scikit-Learn", "Machine Learning", "Deep Learning", 
        "Natural Language Processing", "NLP", "Computer Vision", "Tableau", "Power BI", "Excel", "Apache Spark", "Spark",
        # Cloud & DevOps
        "Docker", "Kubernetes", "AWS", "Amazon Web Services", "Azure", "GCP", "Google Cloud", "Terraform", "Jenkins", 
        "Git", "GitHub", "CI/CD", "Linux",
        # Product & Project Management
        "Agile", "Scrum", "Product Strategy", "Product Management", "A/B Testing", "Jira",
        # Design & UX/UI
        "Figma", "Sketch", "UX", "UI", "User Experience", "User Interface", "Wireframing", "Prototyping",
        # Business/Marketing
        "SEO", "Salesforce", "Google Analytics", "Financial Modeling"
    ]
    
    found_skills = []
    # Clean up text by removing extra whitespaces/newlines
    clean_text = re.sub(r'\s+', ' ', text)
    
    for skill in SKILLS_DATABASE:
        # Use regex with word boundaries (except for special character variations like C++)
        if '+' in skill or '.' in skill:
            pattern = re.escape(skill.replace('\\', ''))
            if re.search(pattern, clean_text, re.IGNORECASE):
                display_name = skill.replace('\\', '')
                if display_name == "Golang":
                    display_name = "Go"
                if display_name not in found_skills:
                    found_skills.append(display_name)
        else:
            pattern = r'\b' + skill + r'\b'
            if re.search(pattern, clean_text, re.IGNORECASE):
                display_name = skill
                if display_name == "Golang":
                    display_name = "Go"
                if display_name not in found_skills:
                    found_skills.append(display_name)
                    
    # Return comma-separated list
    return ", ".join(found_skills)
