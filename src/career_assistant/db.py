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
            skills TEXT,
            resume_markdown TEXT,
            default_resume TEXT
        )
    """)
    
    # Check compatibility for older user_profile schemas
    cursor.execute("PRAGMA table_info(user_profile)")
    columns = [col[1] for col in cursor.fetchall()]
    if "skills" not in columns:
        cursor.execute("ALTER TABLE user_profile ADD COLUMN skills TEXT")
    if "resume_markdown" not in columns:
        cursor.execute("ALTER TABLE user_profile ADD COLUMN resume_markdown TEXT")
    if "defult_resume" in columns:
        cursor.execute("ALTER TABLE user_profile DROP COLUMN defult_resume")
    if "default_resume" not in columns:
        cursor.execute("ALTER TABLE user_profile ADD COLUMN default_resume TEXT")
    
    # Create Jobs Applied table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs_applied (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            date TEXT NOT NULL,
            url TEXT,
            status TEXT DEFAULT 'Applied'
        )
    """)
    
    # Create Jobs To Apply table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs_to_apply (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            url TEXT,
            description TEXT,
            tailored_resume TEXT
        )
    """)
    
    # Check compatibility for older jobs_to_apply schemas
    cursor.execute("PRAGMA table_info(jobs_to_apply)")
    to_apply_cols = [col[1] for col in cursor.fetchall()]
    if "deadline" in to_apply_cols:
        try:
            cursor.execute("ALTER TABLE jobs_to_apply DROP COLUMN deadline")
        except sqlite3.OperationalError:
            # Fallback for older SQLite versions: recreate table without 'deadline'
            cursor.execute("ALTER TABLE jobs_to_apply RENAME TO jobs_to_apply_old")
            cursor.execute("""
                CREATE TABLE jobs_to_apply (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company TEXT NOT NULL,
                    role TEXT NOT NULL,
                    url TEXT,
                    description TEXT,
                    tailored_resume TEXT
                )
            """)
            cursor.execute("""
                INSERT INTO jobs_to_apply (id, company, role, url, description, tailored_resume)
                SELECT id, company, role, url, description, tailored_resume FROM jobs_to_apply_old
            """)
            cursor.execute("DROP TABLE jobs_to_apply_old")
        
        # Fetch updated columns list in case table was recreated or column dropped
        cursor.execute("PRAGMA table_info(jobs_to_apply)")
        to_apply_cols = [col[1] for col in cursor.fetchall()]

    if "description" not in to_apply_cols:
        cursor.execute("ALTER TABLE jobs_to_apply ADD COLUMN description TEXT")
    if "tailored_resume" not in to_apply_cols:
        cursor.execute("ALTER TABLE jobs_to_apply ADD COLUMN tailored_resume TEXT")
        
    # Check compatibility for older jobs_applied schemas
    cursor.execute("PRAGMA table_info(jobs_applied)")
    applied_cols = [col[1] for col in cursor.fetchall()]
    if "status" not in applied_cols:
        cursor.execute("ALTER TABLE jobs_applied ADD COLUMN status TEXT DEFAULT 'Applied'")
    
    conn.commit()
    conn.close()

def save_profile(full_name, desired_role, location, resume_name=None, resume_bytes=None, skills=None, default_resume=None):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Retrieve existing default resume and resume bytes if they exist, to make sure we don't overwrite it
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_profile'")
    existing_default = None
    existing_bytes = None
    if cursor.fetchone():
        try:
            cursor.execute("SELECT default_resume, resume_bytes FROM user_profile LIMIT 1")
            row = cursor.fetchone()
            if row:
                existing_default = row[0]
                existing_bytes = row[1]
        except Exception:
            pass
            
    # Update default_resume only if a new resume is uploaded and parsed in the onboarding process.
    # Otherwise, do not overwrite or update default_resume in the database.
    is_new_resume = (existing_bytes is None and resume_bytes is not None) or (existing_bytes is not None and resume_bytes != existing_bytes)

    if is_new_resume:
        final_default = default_resume if default_resume else existing_default
    else:
        final_default = existing_default if existing_default else default_resume

    # Check if a profile already exists
    cursor.execute("SELECT COUNT(*) FROM user_profile")
    count = cursor.fetchone()[0]
    
    # Delete existing profiles first (single user app)
    cursor.execute("DELETE FROM user_profile")
    cursor.execute("""
        INSERT INTO user_profile (full_name, desired_role, location, resume_name, resume_bytes, skills, default_resume)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (full_name, desired_role, location, resume_name, resume_bytes, skills, final_default))
    
    # If this is the first onboarding, seed the applied tracker with mock jobs matching the target role if empty
    if count == 0:
        # Only seed applied jobs if history is currently empty
        cursor.execute("SELECT COUNT(*) FROM jobs_applied")
        applied_count = cursor.fetchone()[0]
        if applied_count == 0:
            cursor.execute("""
                INSERT INTO jobs_applied (company, role, date, url, status) VALUES 
                ('Google', ?, '2026-06-25', 'https://www.google.com/about/careers/applications/', 'Applied'),
                ('Meta', 'Product Analyst', '2026-06-20', 'https://www.metacareers.com/', 'Applied')
            """, (desired_role,))
        
    conn.commit()
    conn.close()

def get_profile():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT full_name, desired_role, location, resume_name, resume_bytes, skills, resume_markdown, default_resume FROM user_profile LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "full_name": row[0],
            "desired_role": row[1],
            "location": row[2],
            "resume_name": row[3],
            "resume_bytes": row[4],
            "skills": row[5],
            "resume_markdown": row[6],
            "default_resume": row[7]
        }
    return None

def update_resume_markdown(resume_markdown):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE user_profile SET resume_markdown = ?", (resume_markdown,))
    conn.commit()
    conn.close()

def get_resume_markdown():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT resume_markdown FROM user_profile LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0]
    return None

def clear_profile():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_profile")
    # Do not delete jobs_applied or jobs_to_apply to preserve history per user request
    conn.commit()
    conn.close()

def get_jobs_applied():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, company, role, date, url, status FROM jobs_applied ORDER BY date DESC")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "company": r[1], "role": r[2], "date": r[3], "url": r[4], "status": r[5]} for r in rows]

def add_job_applied(company, role, date, url="", status="Applied"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO jobs_applied (company, role, date, url, status)
        VALUES (?, ?, ?, ?, ?)
    """, (company, role, date, url, status))
    conn.commit()
    conn.close()

def update_job_applied(job_id, company, role, date, url="", status="Applied"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE jobs_applied
        SET company = ?, role = ?, date = ?, url = ?, status = ?
        WHERE id = ?
    """, (company, role, date, url, status, job_id))
    conn.commit()
    conn.close()

def update_job_status(job_id, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE jobs_applied
        SET status = ?
        WHERE id = ?
    """, (status, job_id))
    conn.commit()
    conn.close()

def delete_job_applied(job_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        clean_id = int(job_id)
    except (ValueError, TypeError):
        clean_id = job_id
    cursor.execute("DELETE FROM jobs_applied WHERE id = ?", (clean_id,))
    conn.commit()
    conn.close()

def get_jobs_to_apply():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, company, role, url, description, tailored_resume FROM jobs_to_apply ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "company": r[1], "role": r[2], "url": r[3], "description": r[4], "tailored_resume": r[5]} for r in rows]

def add_job_to_apply(company, role, url=""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO jobs_to_apply (company, role, url)
        VALUES (?, ?, ?)
    """, (company, role, url))
    conn.commit()
    conn.close()

def delete_job_to_apply(job_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        clean_id = int(job_id)
    except (ValueError, TypeError):
        clean_id = job_id
    cursor.execute("DELETE FROM jobs_to_apply WHERE id = ?", (clean_id,))
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
            INSERT INTO jobs_applied (company, role, date, url, status)
            VALUES (?, ?, ?, ?, 'Applied')
        """, (company, role, date, url))
        # Delete from to apply
        cursor.execute("DELETE FROM jobs_to_apply WHERE id = ?", (job_id,))
        
    conn.commit()
    conn.close()

def update_job_to_apply_description(job_id, description):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE jobs_to_apply
        SET description = ?
        WHERE id = ?
    """, (description, job_id))
    conn.commit()
    conn.close()

def update_job_to_apply_tailored_resume(job_id, tailored_resume):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE jobs_to_apply
        SET tailored_resume = ?
        WHERE id = ?
    """, (tailored_resume, job_id))
    conn.commit()
    conn.close()
