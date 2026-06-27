import re

import streamlit as st

from services.exa_client import extract_job_listing, search_interview_info
from services.llm_client import call_llm
from services.parsing import safe_parse_json
from services.prompts import (
    INTERVIEW_FEEDBACK_PROMPT,
    INTERVIEW_QUESTION_PROMPT,
    JOB_ANALYSIS_PROMPT,
)
from services.scoring import calculate_dummy_score, calculate_score

st.set_page_config(page_title="Interview Prep", page_icon="🎤", layout="wide")
st.title("Interview Prep")

if "extracted_job" not in st.session_state:
    st.session_state.extracted_job = None
if "keywords" not in st.session_state:
    st.session_state.keywords = []
if "job_analysis" not in st.session_state:
    st.session_state.job_analysis = ""
if "interview_sources" not in st.session_state:
    st.session_state.interview_sources = []
if "questions" not in st.session_state:
    st.session_state.questions = []
if "feedback" not in st.session_state:
    st.session_state.feedback = ""
if "score" not in st.session_state:
    st.session_state.score = calculate_dummy_score()
    
def infer_company_and_role(text: str):
    prompt = """
            Extract the company name and job title from the text below.

            Return JSON:
            {
            "company": "...",
            "role": "..."
            }

            If unknown, use null.
            """

    result = call_llm(prompt, text)
    parsed = safe_parse_json(result)
    return parsed.get("company"), parsed.get("role")

col_url, col_desc = st.columns(2)
with col_url:
    job_url = st.text_input("Job listing URL", placeholder="https://...")
with col_desc:
    job_description = st.text_area(
        "Paste Job Description (used if extraction fails)",
        height=220,
        placeholder="""
    Paste the full job description here if the URL cannot be scraped.

    Example:
    Responsibilities:
    ...

    Requirements:
    ...
    """,
    )

btn_col1, btn_col2 = st.columns(2)
with btn_col1:
    if st.button("Extract Job Listing", use_container_width=True):

        with st.spinner("Extracting job listing..."):

            result = extract_job_listing(job_url)

            st.session_state.extracted_job = result
            st.session_state.keywords = result.get(
                "keywords",
                [],
            )

            if result.get("manual_input_required"):

                st.warning(
                    "⚠️ This job page could not be extracted.\n\n"
                    "Please paste the job description into the box on the right "
                    "and click **Analyze Job**."
                )

            elif result.get("error"):

                st.error(
                    result["error"]
                )

            else:

                st.success(
                    "Job extracted successfully."
                )
with btn_col2:
    if st.button("Analyze Job", use_container_width=True):
        text = (
            job_description.strip()
            or (
                st.session_state.extracted_job
                or {}
            ).get(
                "description",
                ""
            )
        )
        if not text.strip():
            st.warning("Add a job URL or paste a job description first.")
        else:
            with st.spinner("Analyzing job and searching interview sources..."):
                analysis = call_llm(JOB_ANALYSIS_PROMPT, text)
                st.session_state.job_analysis = analysis
                parsed = safe_parse_json(analysis)
                if parsed.get("skills"):
                    st.session_state.keywords = parsed["skills"]
                company = (st.session_state.extracted_job or {}).get("company", "Company")
                role = (st.session_state.extracted_job or {}).get("title", "Role")
                if not company or not role:
                    company, role = infer_company_and_role(text)
                st.session_state.interview_sources = search_interview_info(company, role)

st.subheader("Extracted keywords")
if st.session_state.keywords:
    st.write(", ".join(st.session_state.keywords))
else:
    st.info("Keywords will appear here after extraction or analysis.")

if st.session_state.job_analysis:
    st.subheader("Job analysis")
    parsed = safe_parse_json(st.session_state.job_analysis)
    if parsed.get("summary"):
        st.write(parsed["summary"])
        if parsed.get("seniority"):
            st.caption(f"Seniority: {parsed['seniority']}")
        if parsed.get("responsibilities"):
            st.markdown("**Key responsibilities**")
            for item in parsed["responsibilities"]:
                st.markdown(f"- {item}")
    else:
        st.write(st.session_state.job_analysis)

st.subheader("Online interview sources")
if st.session_state.interview_sources:
    for src in st.session_state.interview_sources:
        st.markdown(f"- [{src.get('title', 'Source')}]({src.get('url', '#')})")
else:
    st.info("Interview research sources will appear here.")

if st.button("Generate Interview Questions", use_container_width=True):
    ctx = job_description or str(st.session_state.extracted_job or {})
    if not ctx.strip() and not st.session_state.job_analysis:
        st.warning("Add a job description or extract a listing first.")
    else:
        with st.spinner("Generating interview questions..."):
            context = f"{ctx}\n\nAnalysis:\n{st.session_state.job_analysis}"
            raw = call_llm(INTERVIEW_QUESTION_PROMPT, context)
            lines = [re.sub(r"^\d+[\).\s]+", "", q.strip()) for q in raw.split("\n") if q.strip()]
            st.session_state.questions = lines[:5]

st.subheader("Practice questions")
answers = {}
for i, q in enumerate(st.session_state.questions or ["(Generate questions first)"]):
    answers[i] = st.text_area(f"Q{i + 1}: {q}", key=f"answer_{i}", height=80)

if st.button("Generate Feedback", use_container_width=True):
    if not st.session_state.questions:
        st.warning("Generate interview questions first.")
    else:
        combined = "\n\n".join(
            f"Q: {q}\nA: {answers.get(i, '')}" for i, q in enumerate(st.session_state.questions)
        )
        with st.spinner("Generating feedback and score..."):
            st.session_state.feedback = call_llm(INTERVIEW_FEEDBACK_PROMPT, combined or "No answers yet.")
            st.session_state.score = calculate_score(combined)

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
