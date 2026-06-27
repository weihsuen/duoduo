import streamlit as st
import pandas as pd

from services.supabase_client import (
    get_applications,
    get_job_listings,
    get_latest_scores_by_job,
    upsert_application,
)

st.set_page_config(page_title="Job Dashboard", page_icon="📊", layout="wide")
st.title("Job Dashboard")

jobs = get_job_listings()
applications = get_applications()
scores = get_latest_scores_by_job()

total_jobs = len(jobs)
apps_sent = sum(1 for a in applications if a.get("status") in ("applied", "interview", "offer", "rejected"))
interviews = sum(1 for a in applications if a.get("status") == "interview")
avg_score = round(sum(s.get("overall", 0) for s in scores) / len(scores), 1) if scores else 0.0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total saved jobs", total_jobs)
c2.metric("Applications sent", apps_sent)
c3.metric("Interviews scheduled", interviews)
c4.metric("Avg preparedness", f"{avg_score}%")

rows = []
for job in jobs:
    app = next((a for a in applications if a.get("job_id") == job.get("id")), {})
    score = next((s for s in scores if s.get("job_id") == job.get("id")), {})
    rows.append(
        {
            "Company": job.get("company", ""),
            "Role": job.get("title", ""),
            "Status": app.get("status", "saved"),
            "Applied": app.get("application_date", ""),
            "Interview": app.get("interview_date", ""),
            "Score": score.get("overall", "—"),
        }
    )

st.subheader("Jobs")
st.dataframe(pd.DataFrame(rows) if rows else pd.DataFrame(columns=["Company", "Role", "Status", "Applied", "Interview", "Score"]), use_container_width=True)

st.subheader("Update application")
with st.form("update_application"):
    job_labels = [f"{j.get('company', '?')} — {j.get('title', '?')}" for j in jobs] or ["Sample Co — Engineer"]
    job_pick = st.selectbox("Job", job_labels)
    status = st.selectbox("Status", ["saved", "applied", "interview", "offer", "rejected"])
    application_date = st.date_input("Application date")
    interview_date = st.date_input("Interview date")
    notes = st.text_area("Notes", height=80)
    submitted = st.form_submit_button("Save")

if submitted:
    job_idx = job_labels.index(job_pick) if job_pick in job_labels else 0
    job_id = jobs[job_idx].get("id") if jobs else "00000000-0000-0000-0000-000000000001"
    upsert_application(
        {
            "job_id": job_id,
            "status": status,
            "application_date": str(application_date),
            "interview_date": str(interview_date),
            "notes": notes,
        }
    )
    st.success("Application updated (placeholder — not persisted yet).")
