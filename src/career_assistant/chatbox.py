import streamlit as st
import requests
import datetime
import os
import re
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

# Helper function to parse user natural language query
def parse_user_query(message, default_role, default_location):
    msg_lower = message.lower().strip()
    
    # Remove common conversational prefixes
    for prefix in ["find me", "show me", "search for", "look for", "find", "search"]:
        if msg_lower.startswith(prefix):
            message = message[len(prefix):].strip()
            msg_lower = message.lower()
            
    # Heuristics: split by " in " or " near " to isolate location
    title = default_role
    location = None
    
    in_match = re.search(r'\s+in\s+', message, flags=re.IGNORECASE)
    near_match = re.search(r'\s+near\s+', message, flags=re.IGNORECASE)
    
    if in_match:
        parts = re.split(r'\s+in\s+', message, maxsplit=1, flags=re.IGNORECASE)
        title = parts[0].strip()
        location = parts[1].strip()
    elif near_match:
        parts = re.split(r'\s+near\s+', message, maxsplit=1, flags=re.IGNORECASE)
        title = parts[0].strip()
        location = parts[1].strip()
    else:
        # Use the whole input as the query title keyword, location defaults to None
        if msg_lower:
            title = message.strip()
            
    # Clean up title if it contains work arrangement keywords
    title_clean = []
    for word in title.split():
        if word.lower() not in ["remote", "hybrid", "jobs", "job", "postings", "posting", "openings", "opening"]:
            title_clean.append(word)
            
    title_result = " ".join(title_clean) if title_clean else title
    
    # If no location was mentioned in the query, load default locations from the SQLite database
    if location is None:
        profile = db.get_profile()
        if profile and profile.get("location"):
            location = profile["location"]
        else:
            location = default_location
            
    return title_result, location

def compute_job_match(job, user_skills):
    if not user_skills:
        return 0, []
        
    title = job.get("title", "") or ""
    description = job.get("description", "") or job.get("snippet", "") or ""
    job_text = f"{title} {description}".lower()
    
    matching = []
    for skill in user_skills:
        skill_clean = skill.strip()
        if not skill_clean:
            continue
        if skill_clean.lower() in ["c++", "c#", ".net"]:
            pattern = re.escape(skill_clean.lower())
        else:
            pattern = r'\b' + re.escape(skill_clean.lower()) + r'\b'
            
        if re.search(pattern, job_text):
            if skill_clean not in matching:
                matching.append(skill_clean)
            
    return len(matching), matching

def fetch_jobs_from_glassdoor_api(title, location, work_arrangement=None):
    rapidapi_host = "glassdoor-real-time.p.rapidapi.com"
    rapidapi_key = os.getenv("RAPIDAPI_KEY")
    
    if not rapidapi_host or not rapidapi_key:
        return "RapidAPI Connection Failure: API host or key not found in environment configurations."
        
    headers = {
        "x-rapidapi-host": rapidapi_host,
        "x-rapidapi-key": rapidapi_key
    }
    
    # 1. Resolve locations to locationIds
    loc_parts = []
    has_remote = False
    if location:
        for loc in location.split("; "):
            loc = loc.strip()
            if not loc:
                continue
            if loc.lower() == "remote":
                has_remote = True
            else:
                loc_parts.append(loc)
                
    location_ids = []
    for loc_name in loc_parts:
        try:
            loc_url = "https://glassdoor-real-time.p.rapidapi.com/jobs/location"
            res = requests.get(loc_url, headers=headers, params={"query": loc_name}, timeout=10)
            if res.status_code == 200:
                data = res.json()
                results = data.get("data", [])
                if results:
                    location_ids.append(results[0].get("locationId"))
        except Exception as e:
            print(f"Error resolving location {loc_name}: {e}")
            
    # 2. Query search endpoint
    search_url = "https://glassdoor-real-time.p.rapidapi.com/jobs/search"
    all_raw_jobs = []
    
    # Check if remote only
    remote_only = False
    if work_arrangement and "remote" in work_arrangement.lower():
        remote_only = True
    elif not location_ids and has_remote:
        remote_only = True
        
    # If we have location IDs, query for each location
    if location_ids:
        for loc_id in location_ids:
            params = {
                "query": title,
                "locationId": loc_id
            }
            if remote_only:
                params["remoteOnly"] = True
            try:
                res = requests.get(search_url, headers=headers, params=params, timeout=10)
                if res.status_code == 200:
                    data = res.json()
                    listings = data.get("data", {}).get("jobListings", [])
                    all_raw_jobs.extend(listings)
            except Exception as e:
                print(f"Error searching jobs for locationId {loc_id}: {e}")
    else:
        # No physical locations resolved, query generally
        params = {
            "query": title
        }
        if remote_only:
            params["remoteOnly"] = True
        try:
            res = requests.get(search_url, headers=headers, params=params, timeout=10)
            if res.status_code == 200:
                data = res.json()
                listings = data.get("data", {}).get("jobListings", [])
                all_raw_jobs.extend(listings)
        except Exception as e:
            return f"RapidAPI Connection Failure: Unable to query search API. Error: {str(e)}"
            
    # Deduplicate and map raw jobs
    seen_ids = set()
    mapped_jobs = []
    
    for item in all_raw_jobs:
        jobview = item.get("jobview", {})
        header = jobview.get("header", {})
        job_info = jobview.get("job", {})
        
        job_id = str(job_info.get("listingId") or header.get("jobResultTrackingKey") or "gd_" + str(len(mapped_jobs)))
        if job_id in seen_ids:
            continue
        seen_ids.add(job_id)
        
        org = header.get("employerNameFromSearch") or header.get("employer", {}).get("name") or "Unknown Company"
        job_title = job_info.get("jobTitleText") or "Unknown Role"
        
        url_suffix = header.get("jobViewUrl") or ""
        job_url = f"https://www.glassdoor.com{url_suffix}" if url_suffix else ""
        
        age = header.get("ageInDays")
        date_str = f"Posted {age} days ago" if age is not None else "Active"
        
        # Determine arrangement
        arrangement = "N/A"
        loc_name = header.get("locationName") or "US"
        attrs = header.get("indeedJobAttribute", {}).get("extractedJobAttributes", [])
        is_remote = False
        is_hybrid = False
        for attr in attrs:
            val = str(attr.get("value", "")).lower()
            if "remote" in val:
                is_remote = True
            if "hybrid" in val:
                is_hybrid = True
                
        if is_remote or "remote" in loc_name.lower():
            arrangement = "Remote"
        elif is_hybrid or "hybrid" in loc_name.lower():
            arrangement = "Hybrid"
        else:
            arrangement = "On-site"
            
        # Collect extracted job attributes to form a descriptive text for matching
        attr_values = [str(attr.get("value", "")) for attr in attrs if attr.get("value")]
        desc_text = " ".join(attr_values)
            
        mapped_jobs.append({
            "organization": org,
            "title": job_title,
            "url": job_url,
            "id": job_id,
            "date_created": date_str,
            "ai_work_arrangement": arrangement,
            "locations_derived": [loc_name],
            "description": desc_text
        })
        
    return mapped_jobs

# API Client calling the Active Jobs DB API
def fetch_jobs_from_api(title, location, work_arrangement=None, time_frame="24h"):
    url = "https://active-jobs-db.p.rapidapi.com/active-ats"
    
    # Retrieve credentials using os.getenv()
    rapidapi_host = os.getenv("RAPIDAPI_HOST")
    rapidapi_key = os.getenv("RAPIDAPI_KEY")
    
    if not rapidapi_host or not rapidapi_key:
        return "RapidAPI Connection Failure: API host or key not found in environment configurations."
        
    headers = {
        "x-rapidapi-host": rapidapi_host,
        "x-rapidapi-key": rapidapi_key
    }
    
    params = {
        "time_frame": time_frame, # Window for fresh postings
        "limit": "5",       # Less than 6 at a time (strict limit)
        "title": title
    }
    
    # Exclude remote word from literal location search and handle multiple preferences
    if location:
        loc_parts = [loc.strip() for loc in location.split("; ") if loc.strip().lower() != "remote"]
        if loc_parts:
            params["location"] = " OR ".join(loc_parts)
        
    if work_arrangement:
        params["ai_work_arrangement"] = work_arrangement

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return f"RapidAPI Connection Failure: API returned status code {response.status_code}. {response.text}"
    except Exception as e:
        return f"RapidAPI Connection Failure: Unable to reach endpoint. Error: {str(e)}"

# API Client calling the LinkedIn Job Search API
def fetch_jobs_from_linkedin_api(title, location, work_arrangement=None, time_frame="24h"):
    url = "https://linkedin-job-search-api.p.rapidapi.com/active-jb"
    
    # Retrieve credentials using os.getenv()
    rapidapi_key = os.getenv("RAPIDAPI_KEY")
    
    if not rapidapi_key:
        return "RapidAPI Connection Failure: API key not found in environment configurations."
        
    headers = {
        "x-rapidapi-host": "linkedin-job-search-api.p.rapidapi.com",
        "x-rapidapi-key": rapidapi_key
    }
    
    params = {
        "time_frame": time_frame, # Window for fresh postings
        "limit": "20",       # Less than 6 at a time (strict limit)
        "title": title
    }
    
    # Process location filter for LinkedIn API
    if location:
        loc_parts = []
        for loc in location.split("; "):
            loc = loc.strip()
            if not loc:
                continue
            if loc.lower() == "remote":
                continue
            # Normalize US and UK
            if loc.lower() == "us":
                loc = "United States"
            elif loc.lower() == "uk":
                loc = "United Kingdom"
            loc_parts.append(f'"{loc}"')
            
        if loc_parts:
            params["location"] = " OR ".join(loc_parts)
        else:
            params["location"] = "United States"
            
    if work_arrangement:
        params["ai_work_arrangement"] = work_arrangement

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            raw_jobs = response.json()
            if not isinstance(raw_jobs, list):
                return "RapidAPI Connection Failure: Unexpected response format from LinkedIn API."
            
            mapped_jobs = []
            for job in raw_jobs:
                job_id = str(job.get("id") or job.get("linkedin_id") or f"li_{len(mapped_jobs)}")
                org = job.get("organization") or "Unknown Company"
                job_title = job.get("title") or "Unknown Role"
                job_url = job.get("url") or ""
                
                # Retrieve date_created or date_posted. LinkedIn API has both.
                date_created = job.get("date_created") or job.get("date_posted") or "Active"
                if "T" in date_created:
                    try:
                        date_created = date_created.split("T")[0]
                    except:
                        pass
                
                arrangement = job.get("ai_work_arrangement") or "N/A"
                
                # Derive location string
                locs_derived = job.get("locations_derived", [])
                if not locs_derived:
                    locations_list = job.get("locations", [])
                    if locations_list:
                        addr = locations_list[0].get("address", {})
                        city = addr.get("addressLocality")
                        region = addr.get("addressRegion")
                        country = addr.get("addressCountry")
                        loc_str = ", ".join(filter(None, [city, region, country]))
                        if loc_str:
                            locs_derived = [loc_str]
                if not locs_derived:
                    locs_derived = ["N/A"]
                    
                # Build description for skill matching
                skills_str = ", ".join(job.get("ai_key_skills", []))
                req_sum = job.get("ai_requirements_summary", "")
                core_resp = job.get("ai_core_responsibilities", "")
                description = f"{skills_str} {req_sum} {core_resp}".strip()
                
                mapped_jobs.append({
                    "organization": org,
                    "title": job_title,
                    "url": job_url,
                    "id": job_id,
                    "date_created": date_created,
                    "ai_work_arrangement": arrangement,
                    "locations_derived": locs_derived,
                    "description": description
                })
            return mapped_jobs
        else:
            return f"RapidAPI Connection Failure: API returned status code {response.status_code}. {response.text}"
    except Exception as e:
        return f"RapidAPI Connection Failure: Unable to reach endpoint. Error: {str(e)}"


# Primary chatbox renderer
def render_chatbox():
    st.markdown("### 💬 Live Job Search Assistant")
    
    col_lbl, col_switch = st.columns([1, 1])
    with col_lbl:
        st.markdown("Ask the assistant to query live postings:")
    with col_switch:
        mcp_source = st.selectbox(
            "Job Database Source",
            options=["Glassdoor (Real-Time)", "Active Jobs DB", "LinkedIn jobs"],
            index=0,
            key="chat_mcp_source",
            label_visibility="collapsed"
        )

    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {
                "role": "assistant",
                "content": "Hi! Ask me about new job postings. I will query the selected database. You can search by title and location, e.g. 'find python jobs in New York'."
            }
        ]

    # Render previous messages
    for msg_idx, msg in enumerate(st.session_state.chat_history):
        with st.chat_message(msg["role"]):
            col_text, col_del = st.columns([9, 1])
            with col_text:
                st.write(msg["content"])
            with col_del:
                if st.button("🗑️", key=f"del_msg_{msg_idx}", type="secondary", help="Delete this message"):
                    st.session_state.chat_history.pop(msg_idx)
                    st.rerun()
            
            # If the assistant message contains job listings, render them
            if "jobs" in msg and msg["jobs"]:
                for job_idx, job in enumerate(msg["jobs"]):
                    job_url = job.get('url', '')
                    url_html = f'<div style="margin-top: 0.25rem;"><a href="{job_url}" target="_blank" style="color: #4A5D4E; text-decoration: none; font-weight: 600; font-size: 0.85rem;">🔗 View Job Posting</a></div>' if job_url else ""
                    arrangement = job.get("ai_work_arrangement", "N/A")
                    location_val = job.get('locations_derived', ['N/A'])
                    location_str = location_val[0] if isinstance(location_val, list) and len(location_val) > 0 else "N/A"
                    
                    # Recommendation Badge
                    match_score = job.get("match_score", 0)
                    matched_skills = job.get("matched_skills", [])
                    if match_score > 0:
                        matched_skills_str = ", ".join(matched_skills)
                        badge_html = f'<div style="background-color: #EBF2EC; border: 1px solid #D1E2D5; border-radius: 6px; padding: 0.3rem 0.6rem; margin-bottom: 0.6rem; font-size: 0.8rem; color: #3B4B3F; font-weight: 600; display: inline-flex; align-items: center; gap: 0.3rem;">⭐️ Tailored Recommendation (Matches: {matched_skills_str})</div>'
                    else:
                        badge_html = ""
                        
                    html_content = (
                        f'<div class="job-card" style="background-color: #FAF8F5; border-radius: 8px; padding: 0.9rem; border: 1px solid #EFE8DD; margin-bottom: 0.5rem;">'
                        f'{badge_html}'
                        f'<div class="job-company">{job["organization"]} &nbsp;|&nbsp; 📍 {location_str}</div>'
                        f'<div class="job-title" style="font-size: 0.95rem; font-weight: 600; color: #4A5D4E;">{job["title"]}</div>'
                        f'<div class="job-meta">Arrangement: {arrangement}</div>'
                        f'<div style="font-size: 0.72rem; color: #718096; margin-top: 0.2rem; font-family: monospace;">'
                        f'Verified ID: {job["id"]} | Ingested: {job["date_created"]}</div>'
                        f'{url_html}'
                        f'</div>'
                    )
                    st.markdown(html_content, unsafe_allow_html=True)
                    
                    # Add to Plan Button
                    if st.button("➕ Add to Plan", key=f"chat_add_{msg_idx}_{job_idx}_{job['id']}", type="secondary", use_container_width=True):
                        # Save job to database
                        db.add_job_to_apply(
                            company=job['organization'],
                            role=job['title'],
                            url=job.get('url', '')
                        )
                        st.success(f"Added '{job['title']}' at {job['organization']} to your Jobs To Apply tracker!")
                        st.rerun()

    # Chat input box
    if user_input := st.chat_input("Ask about new job postings...", key="job_chat_input"):
        # Append user query to history
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        st.session_state.awaiting_assistant_response = True
        
        # Rerun to draw user message and trigger assistant response
        st.rerun()

    # Trigger assistant response if the last message is from user
    if st.session_state.chat_history[-1]["role"] == "user" and st.session_state.get("awaiting_assistant_response", False):
        st.session_state.awaiting_assistant_response = False
        user_msg = st.session_state.chat_history[-1]["content"]
        
        default_role = st.session_state.get("desired_role", "Data Analyst")
        default_location = st.session_state.get("location", "Remote")
        
        parsed_title, parsed_location = parse_user_query(user_msg, default_role, default_location)
        
        # Detect work arrangements in user prompt
        work_arrangement = None
        lower_msg = user_msg.lower()
        if "remote" in lower_msg:
            work_arrangement = "Remote OK,Remote Solely"
        elif "hybrid" in lower_msg:
            work_arrangement = "Hybrid"
            
        source = st.session_state.get("chat_mcp_source", "Glassdoor (Real-Time)")
        with st.chat_message("assistant"):
            with st.spinner(f"Querying live {source} Database..."):
                results = None
                time_frame = "24h"
                if source == "Glassdoor (Real-Time)":
                    results = fetch_jobs_from_glassdoor_api(parsed_title, parsed_location, work_arrangement)
                elif source == "Active Jobs DB":
                    results = fetch_jobs_from_api(parsed_title, parsed_location, work_arrangement, time_frame=time_frame)
                elif source == "LinkedIn jobs":
                    results = fetch_jobs_from_linkedin_api(parsed_title, parsed_location, work_arrangement, time_frame=time_frame)
                else:
                    results = f"Unknown job database source: {source}"
                
            if isinstance(results, str):
                # Connection error or other API failure
                st.error(results)
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": f"⚠️ Error ({source}): {results}"
                })
            else:
                # Succeeded
                jobs_list = results
                if isinstance(jobs_list, list):
                    # Score and rank jobs based on resume skills
                    user_skills = [s.strip() for s in st.session_state.get("skills", "").split(",") if s.strip()]
                    for job in jobs_list:
                        score, matched = compute_job_match(job, user_skills)
                        job["match_score"] = score
                        job["matched_skills"] = matched
                    # Sort results: jobs with higher match score first
                    jobs_list.sort(key=lambda x: x.get("match_score", 0), reverse=True)
                    # Enforce strict maximum limit of 5 jobs
                    jobs_list = jobs_list[:5]
                    
                if not jobs_list:
                    if source == "Glassdoor (Real-Time)":
                        response_text = f"I searched the active {source} database for **{parsed_title}** in **{parsed_location}** but found no new postings."
                    else:
                        response_text = f"I searched the active {source} database for **{parsed_title}** in **{parsed_location}** but found no new postings in the last {time_frame}."
                    st.write(response_text)
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": response_text
                    })
                else:
                    count = len(jobs_list)
                    response_text = f"I found {count} active postings in the {source} database matching **{parsed_title}** in **{parsed_location}**:"
                    st.write(response_text)
                    
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": response_text,
                        "jobs": jobs_list
                    })
            # Re-draw page to display assistant reply
            st.rerun()
