"""Placeholder Supabase client. Returns dummy data when not configured."""

# TODO: Initialize real Supabase client from st.secrets or env vars


def get_supabase_client():
    # TODO: return create_client(SUPABASE_URL, SUPABASE_KEY)
    return None


def save_job_listing(job_data: dict) -> dict:
    # TODO: INSERT into job_listings
    return {**job_data, "id": "00000000-0000-0000-0000-000000000001"}


def get_job_listings() -> list:
    # TODO: SELECT * FROM job_listings ORDER BY created_at DESC
    return [
        {
            "id": "00000000-0000-0000-0000-000000000001",
            "company": "Example Corp",
            "title": "Software Engineer",
            "url": "https://example.com/jobs/1",
        }
    ]


def save_interview_session(session_data: dict) -> dict:
    # TODO: INSERT into interview_sessions
    return session_data


def save_resume(resume_data: dict) -> dict:
    # TODO: INSERT into resumes
    return resume_data


def get_latest_scores_by_job() -> list:
    # TODO: Query latest interview_sessions per job_id
    return [{"job_id": "00000000-0000-0000-0000-000000000001", "overall": 72}]


def upsert_application(application_data: dict) -> dict:
    # TODO: UPSERT into applications
    return application_data


def get_applications() -> list:
    # TODO: SELECT * FROM applications
    return [
        {
            "job_id": "00000000-0000-0000-0000-000000000001",
            "status": "saved",
            "application_date": "",
            "interview_date": "",
            "notes": "",
        }
    ]
