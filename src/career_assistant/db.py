import sqlite3
import os

# Locate the database file in the data directory
current_dir = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.abspath(os.path.join(current_dir, "..", "..", "data", "career_assistant.db"))

# Ensure the parent directory exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Migrate old profile table to user_profile if exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='profile'")
    if cursor.fetchone():
        cursor.execute("ALTER TABLE profile RENAME TO user_profile")

    # Create User Profile table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            desired_role TEXT NOT NULL,
            location TEXT NOT NULL,
            resume_name TEXT,
            resume_bytes BLOB,
            skills TEXT
        )
    """)
    
    # Check compatibility for older user_profile schemas
    cursor.execute("PRAGMA table_info(user_profile)")
    columns = [col[1] for col in cursor.fetchall()]
    if "skills" not in columns:
        cursor.execute("ALTER TABLE user_profile ADD COLUMN skills TEXT")
    
    # Create Jobs Applied table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs_applied (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            date TEXT NOT NULL,
            url TEXT
        )
    """)
    
    # Create Jobs To Apply table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs_to_apply (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            deadline TEXT NOT NULL,
            url TEXT
        )
    """)
    
    conn.commit()
    conn.close()

def save_profile(full_name, desired_role, location, resume_name=None, resume_bytes=None, skills=None):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if a profile already exists
    cursor.execute("SELECT COUNT(*) FROM user_profile")
    count = cursor.fetchone()[0]
    
    # Delete existing profiles first (single user app)
    cursor.execute("DELETE FROM user_profile")
    cursor.execute("""
        INSERT INTO user_profile (full_name, desired_role, location, resume_name, resume_bytes, skills)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (full_name, desired_role, location, resume_name, resume_bytes, skills))
    
    # If this is the first onboarding, seed the trackers with mock jobs matching the target role
    if count == 0:
        cursor.execute("""
            INSERT INTO jobs_applied (company, role, date, url) VALUES 
            ('Google', ?, '2026-06-25', 'https://www.google.com/about/careers/applications/'),
            ('Meta', 'Product Analyst', '2026-06-20', 'https://www.metacareers.com/')
        """, (desired_role,))
        
        cursor.execute("""
            INSERT INTO jobs_to_apply (company, role, deadline, url) VALUES 
            ('Netflix', 'Senior ' || ?, '2026-07-15', 'https://jobs.netflix.com/'),
            ('Apple', 'Data Quality Analyst', '2026-07-20', 'https://www.apple.com/careers/')
        """, (desired_role,))
        
    conn.commit()
    conn.close()

def get_profile():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT full_name, desired_role, location, resume_name, resume_bytes, skills FROM user_profile LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "full_name": row[0],
            "desired_role": row[1],
            "location": row[2],
            "resume_name": row[3],
            "resume_bytes": row[4],
            "skills": row[5]
        }
    return None

def clear_profile():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_profile")
    cursor.execute("DELETE FROM jobs_applied")
    cursor.execute("DELETE FROM jobs_to_apply")
    conn.commit()
    conn.close()

def get_jobs_applied():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, company, role, date, url FROM jobs_applied ORDER BY date DESC")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "company": r[1], "role": r[2], "date": r[3], "url": r[4]} for r in rows]

def add_job_applied(company, role, date, url=""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO jobs_applied (company, role, date, url)
        VALUES (?, ?, ?, ?)
    """, (company, role, date, url))
    conn.commit()
    conn.close()

def update_job_applied(job_id, company, role, date, url=""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE jobs_applied
        SET company = ?, role = ?, date = ?, url = ?
        WHERE id = ?
    """, (company, role, date, url, job_id))
    conn.commit()
    conn.close()

def delete_job_applied(job_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM jobs_applied WHERE id = ?", (job_id,))
    conn.commit()
    conn.close()

def get_jobs_to_apply():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, company, role, deadline, url FROM jobs_to_apply ORDER BY deadline ASC")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "company": r[1], "role": r[2], "deadline": r[3], "url": r[4]} for r in rows]

def add_job_to_apply(company, role, deadline, url=""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO jobs_to_apply (company, role, deadline, url)
        VALUES (?, ?, ?, ?)
    """, (company, role, deadline, url))
    conn.commit()
    conn.close()

def delete_job_to_apply(job_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM jobs_to_apply WHERE id = ?", (job_id,))
    conn.commit()
    conn.close()

def move_to_applied(job_id, date):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Retrieve details from planned table
    cursor.execute("SELECT company, role, url FROM jobs_to_apply WHERE id = ?", (job_id,))
    row = cursor.fetchone()
    if row:
        company, role, url = row
        # Add to applied
        cursor.execute("""
            INSERT INTO jobs_applied (company, role, date, url)
            VALUES (?, ?, ?, ?)
        """, (company, role, date, url))
        # Delete from to apply
        cursor.execute("DELETE FROM jobs_to_apply WHERE id = ?", (job_id,))
        
    conn.commit()
    conn.close()
