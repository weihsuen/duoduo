import streamlit as st

st.set_page_config(page_title="IntervieWhiz.AI", page_icon="🎯", layout="wide")

st.title("IntervieWhiz.AI")
st.caption("Hackathon MVP — interview prep, resume tailoring, and job tracking in one place.")

st.markdown(
    """
    IntervieWhiz.AI helps you prepare for interviews, tailor your resume to a role,
    and track applications from a single dashboard.
    """
)

st.subheader("Pages")
st.markdown(
    """
    1. **Interview Prep** — Extract a job listing, analyze requirements, practice questions, and get feedback.
    2. **Resume Prep** — Generate a tailored resume from your experience bank and a saved job.
    3. **Job Dashboard** — Track saved jobs, applications, interviews, and preparedness scores.
    """
)

st.subheader("MVP checklist")
st.markdown(
    """
    - [ ] Connect Supabase and run `db/schema.sql`
    - [ ] Wire Exa for job listing extraction and interview research
    - [ ] Wire OpenAI for analysis, questions, feedback, and resume generation
    - [ ] Replace placeholder services with real persistence
    - [ ] Deploy to [Zo Computer](https://zocomputer.com) (or similar Streamlit host)
    """
)
