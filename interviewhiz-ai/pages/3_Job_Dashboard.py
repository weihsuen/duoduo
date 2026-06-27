from datetime import date, datetime

import pandas as pd
import streamlit as st

from services.supabase_client import (
    get_applications,
    get_job_listings,
    get_latest_scores_by_job,
    upsert_application,
)


st.set_page_config(page_title="Job Dashboard", page_icon="📊", layout="wide")
st.title("Job Search Dashboard")


def parse_date(value):
    if not value:
        return None

    if isinstance(value, date):
        return value

    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except Exception:
        return None


def days_since(value):
    parsed = parse_date(value)

    if not parsed:
        return "—"

    days = (date.today() - parsed).days

    if days == 0:
        return "Today"

    if days == 1:
        return "1 day ago"

    if days < 0:
        return f"In {abs(days)} days"

    return f"{days} days ago"


def score_display(value):
    if value is None:
        return "—"

    try:
        return f"{float(value):.1f}%"
    except Exception:
        return str(value)


# Load data
jobs = get_job_listings()
applications = get_applications()
scores = get_latest_scores_by_job()


applications_by_job = {
    app.get("job_id"): app
    for app in applications
    if app.get("job_id")
}

scores_by_job = {
    score.get("job_id"): score
    for score in scores
    if score.get("job_id")
}


# Metrics
total_jobs = len(jobs)

apps_sent = sum(
    1
    for app in applications
    if app.get("status") in ["applied", "interview", "offer", "rejected"]
)

interviews = sum(
    1
    for app in applications
    if app.get("status") == "interview"
)

valid_scores = []

for score in scores:
    overall = score.get("overall")

    if overall is None:
        continue

    try:
        valid_scores.append(float(overall))
    except Exception:
        pass

avg_score = round(sum(valid_scores) / len(valid_scores), 1) if valid_scores else 0.0


c1, c2, c3, c4 = st.columns(4)

c1.metric("Total saved jobs", total_jobs)
c2.metric("Applications sent", apps_sent)
c3.metric("Interviews scheduled", interviews)
c4.metric("Avg preparedness", f"{avg_score}%")


# Dashboard table
rows = []

for job in jobs:
    job_id = job.get("id")
    app = applications_by_job.get(job_id, {})
    score = scores_by_job.get(job_id, {})

    rows.append(
        {
            "Company": job.get("company", ""),
            "Role": job.get("title", ""),
            "Status": app.get("status", "saved"),
            "Application date": app.get("application_date") or "—",
            "Days since application": days_since(app.get("application_date")),
            "Interview date": app.get("interview_date") or "—",
            "Days since interview": days_since(app.get("interview_date")),
            "Preparedness": score_display(score.get("overall")),
            "Notes": app.get("notes", ""),
        }
    )


st.subheader("Jobs")

df = pd.DataFrame(
    rows,
    columns=[
        "Company",
        "Role",
        "Status",
        "Application date",
        "Days since application",
        "Interview date",
        "Days since interview",
        "Preparedness",
        "Notes",
    ],
)

st.dataframe(df, use_container_width=True, hide_index=True)


# Update form
st.subheader("Update application")

if not jobs:
    st.info("No job listings saved yet. Save a job listing first.")
    st.stop()


job_labels = [
    f"{job.get('company', 'Unknown Company')} — {job.get('title', 'Unknown Role')}"
    for job in jobs
]

# Keep job picker OUTSIDE the form so changing job updates immediately
job_pick = st.selectbox("Job", job_labels)

selected_index = job_labels.index(job_pick)
selected_job = jobs[selected_index]
selected_job_id = selected_job.get("id")

existing_app = applications_by_job.get(selected_job_id, {})

existing_application_date = parse_date(existing_app.get("application_date"))
existing_interview_date = parse_date(existing_app.get("interview_date"))

with st.form("update_application"):
    status_options = ["saved", "applied", "interview", "offer", "rejected"]
    existing_status = existing_app.get("status", "saved")

    status = st.selectbox(
        "Status",
        status_options,
        index=status_options.index(existing_status)
        if existing_status in status_options
        else 0,
    )

    # Always show the date inputs.
    # The checkbox only controls whether the date is saved.
    has_application_date = st.checkbox(
        "Save application date",
        value=existing_application_date is not None,
    )

    application_date = st.date_input(
        "Application date",
        value=existing_application_date or date.today(),
    )

    has_interview_date = st.checkbox(
        "Save interview date",
        value=existing_interview_date is not None,
    )

    interview_date = st.date_input(
        "Interview date",
        value=existing_interview_date or date.today(),
    )

    notes = st.text_area(
        "Notes",
        value=existing_app.get("notes", ""),
        height=100,
        placeholder="Example: Applied through LinkedIn. Recruiter replied. Need to prepare behavioral questions.",
    )

    submitted = st.form_submit_button("Save")


if submitted:
    upsert_application(
        {
            "job_id": selected_job_id,
            "status": status,
            "application_date": str(application_date) if has_application_date else None,
            "interview_date": str(interview_date) if has_interview_date else None,
            "notes": notes,
        }
    )

    st.success("Application updated.")
    st.rerun()