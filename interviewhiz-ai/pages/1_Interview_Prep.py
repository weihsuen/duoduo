import streamlit as st

from services.exa_client import extract_job_listing, search_interview_info
from services.llm_client import call_llm
from services.prompts import (
    INTERVIEW_FEEDBACK_PROMPT,
    INTERVIEW_QUESTION_PROMPT,
    JOB_ANALYSIS_PROMPT,
)
from services.scoring import calculate_dummy_score

st.set_page_config(page_title="Interview Prep", page_icon="🎤", layout="wide")
st.title("Interview Prep")

if "extracted_job" not in st.session_state:
    st.session_state.extracted_job = None
if "keywords" not in st.session_state:
    st.session_state.keywords = []
if "interview_sources" not in st.session_state:
    st.session_state.interview_sources = []
if "questions" not in st.session_state:
    st.session_state.questions = []
if "feedback" not in st.session_state:
    st.session_state.feedback = ""
if "score" not in st.session_state:
    st.session_state.score = calculate_dummy_score()

col_url, col_desc = st.columns(2)
with col_url:
    job_url = st.text_input("Job listing URL", placeholder="https://...")
with col_desc:
    job_description = st.text_area(
        "Manual job description (optional)",
        height=120,
        placeholder="Paste job description if you don't have a URL.",
    )

btn_col1, btn_col2 = st.columns(2)
with btn_col1:
    if st.button("Extract Job Listing", use_container_width=True):
        st.session_state.extracted_job = extract_job_listing(job_url or "")
        st.session_state.keywords = st.session_state.extracted_job.get("keywords", [])
with btn_col2:
    if st.button("Analyze Job", use_container_width=True):
        text = job_description or (st.session_state.extracted_job or {}).get("description", "")
        _ = call_llm(JOB_ANALYSIS_PROMPT, text)
        company = (st.session_state.extracted_job or {}).get("company", "Company")
        role = (st.session_state.extracted_job or {}).get("title", "Role")
        st.session_state.interview_sources = search_interview_info(company, role)

st.subheader("Extracted keywords")
if st.session_state.keywords:
    st.write(", ".join(st.session_state.keywords))
else:
    st.info("Keywords will appear here after extraction or analysis.")

st.subheader("Online interview sources")
if st.session_state.interview_sources:
    for src in st.session_state.interview_sources:
        st.markdown(f"- [{src.get('title', 'Source')}]({src.get('url', '#')})")
else:
    st.info("Interview research sources will appear here.")

if st.button("Generate Interview Questions", use_container_width=True):
    ctx = job_description or str(st.session_state.extracted_job or {})
    raw = call_llm(INTERVIEW_QUESTION_PROMPT, ctx)
    st.session_state.questions = [q.strip() for q in raw.split("\n") if q.strip()][:5]

st.subheader("Practice questions")
answers = {}
for i, q in enumerate(st.session_state.questions or ["(Generate questions first)"]):
    answers[i] = st.text_area(f"Q{i + 1}: {q}", key=f"answer_{i}", height=80)

if st.button("Generate Feedback", use_container_width=True):
    combined = "\n\n".join(f"Q: {q}\nA: {answers.get(i, '')}" for i, q in enumerate(st.session_state.questions))
    st.session_state.feedback = call_llm(INTERVIEW_FEEDBACK_PROMPT, combined or "No answers yet.")
    st.session_state.score = calculate_dummy_score()

if st.session_state.feedback:
    st.subheader("Feedback")
    st.write(st.session_state.feedback)

st.subheader("Preparedness dashboard")
score = st.session_state.score
m1, m2, m3 = st.columns(3)
m1.metric("Overall score", f"{score['overall']}%")
m2.metric("Technical", f"{score['technical']}%")
m3.metric("Behavioral", f"{score['behavioral']}%")
st.progress(score["overall"] / 100, text="Overall preparedness")

with st.expander("Stretch: audio upload (not implemented)"):
    st.file_uploader("Upload practice answer audio", type=["mp3", "wav", "m4a"], disabled=True)
    st.caption("Voice transcription is a stretch feature for later.")
