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
from services.supabase_client import (
    get_supabase_client,
    save_interview_session,   # ⬅️ ADD THIS (see supabase fix below)
)

# ----------------------------
# PAGE CONFIG
# ----------------------------
st.set_page_config(page_title="Interview Prep", page_icon="🎤", layout="wide")
st.title("Interview Prep")

# ----------------------------
# SESSION STATE INIT
# ----------------------------
defaults = {
    "extracted_job": None,
    "keywords": [],
    "job_analysis": "",
    "interview_sources": [],
    "questions": [],
    "answers": {},   # ✅ FIX: persistent answers
    "feedback": "",
    "score": calculate_dummy_score(),
    "job_analyzed": False,
    "questions_generated": False,
    "feedback_generated": False,
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ----------------------------
# HELPERS
# ----------------------------
def infer_company_and_role(text: str):
    prompt = """
    Extract company name and job title.

    Return JSON:
    {"company":"...","role":"..."}

    If unknown use null.
    """
    result = call_llm(prompt, text)
    parsed = safe_parse_json(result)
    return parsed.get("company"), parsed.get("role")


def reset_pipeline():
    st.session_state.questions = []
    st.session_state.answers = {}
    st.session_state.feedback = ""
    st.session_state.questions_generated = False
    st.session_state.feedback_generated = False


# ----------------------------
# INPUTS
# ----------------------------
col_url, col_desc = st.columns(2)

with col_url:
    job_url = st.text_input("Job listing URL", placeholder="https://...")

with col_desc:
    job_description = st.text_area("Paste Job Description", height=220)


# ----------------------------
# STEP 1: EXTRACT
# ----------------------------
if st.button("Extract Job Listing", use_container_width=True):
    with st.spinner("Extracting..."):
        result = extract_job_listing(job_url)

        st.session_state.extracted_job = result
        st.session_state.keywords = result.get("keywords", [])

        st.success("Extracted.")


# ----------------------------
# STEP 2: ANALYZE
# ----------------------------
if st.button("Analyze Job", use_container_width=True):
    text = job_description.strip() or (
        st.session_state.extracted_job or {}
    ).get("description", "")

    if not text.strip():
        st.warning("Add job input first.")
    else:
        with st.spinner("Analyzing..."):
            analysis = call_llm(JOB_ANALYSIS_PROMPT, text)
            st.session_state.job_analysis = analysis

            parsed = safe_parse_json(analysis)
            if parsed.get("skills"):
                st.session_state.keywords = parsed["skills"]

            company = (st.session_state.extracted_job or {}).get("company")
            role = (st.session_state.extracted_job or {}).get("title")

            if not company or not role:
                company, role = infer_company_and_role(text)

            st.session_state.interview_sources = search_interview_info(company, role)

            st.session_state.job_analyzed = True
            reset_pipeline()


# ----------------------------
# STEP 3: ANALYSIS OUTPUT
# ----------------------------
if st.session_state.job_analyzed:

    st.divider()
    st.subheader("Keywords")
    st.write(", ".join(st.session_state.keywords))

    st.subheader("Analysis")
    parsed = safe_parse_json(st.session_state.job_analysis)
    st.write(parsed.get("summary") or st.session_state.job_analysis)

    st.subheader("Sources")
    for src in st.session_state.interview_sources:
        st.markdown(f"- [{src.get('title')}]({src.get('url')})")


# ----------------------------
# STEP 4: QUESTIONS
# ----------------------------
if st.button("Generate Questions", use_container_width=True):

    ctx = job_description or str(st.session_state.extracted_job or {})

    with st.spinner("Generating..."):
        raw = call_llm(
            INTERVIEW_QUESTION_PROMPT,
            f"{ctx}\n\n{st.session_state.job_analysis}"
        )

        questions = [
            re.sub(r"^\d+[\).\s]+", "", q.strip())
            for q in raw.split("\n")
            if q.strip()
        ][:5]

        st.session_state.questions = questions
        st.session_state.questions_generated = True


# ----------------------------
# STEP 5: QUESTIONS UI
# ----------------------------
if st.session_state.questions_generated:

    st.divider()
    st.subheader("Practice Questions")

    for i, q in enumerate(st.session_state.questions):
        st.session_state.answers[i] = st.text_area(
            f"Q{i+1}: {q}",
            value=st.session_state.answers.get(i, ""),
            key=f"ans_{i}",
            height=80,
        )


# ----------------------------
# STEP 6: FEEDBACK + SAVE
# ----------------------------
if st.button("Generate Feedback", use_container_width=True):

    if not st.session_state.questions:
        st.warning("Generate questions first.")
    else:
        combined = "\n\n".join(
            f"Q: {q}\nA: {st.session_state.answers.get(i, '')}"
            for i, q in enumerate(st.session_state.questions)
        )

        with st.spinner("Scoring..."):
            feedback = call_llm(INTERVIEW_FEEDBACK_PROMPT, combined)
            score = calculate_score(combined)

            st.session_state.feedback = feedback
            st.session_state.score = score
            st.session_state.feedback_generated = True

            # ----------------------------
            # SAVE TO SUPABASE
            # ----------------------------
            try:
                job_id = (st.session_state.extracted_job or {}).get("id")

                save_interview_session({
                    "job_id": job_id,
                    "questions": st.session_state.questions,
                    "answers": [st.session_state.answers.get(i, "") for i in range(len(st.session_state.questions))],
                    "feedback": feedback,
                    "scores": score,
                })
            except Exception as e:
                st.warning(f"DB save failed: {e}")


# ----------------------------
# STEP 7: RESULTS
# ----------------------------
if st.session_state.feedback_generated:

    st.divider()
    st.subheader("Feedback")
    st.write(st.session_state.feedback)

    st.subheader("Preparedness")

    score = st.session_state.score
    c1, c2, c3 = st.columns(3)

    c1.metric("Overall", f"{score['overall']}%")
    c2.metric("Technical", f"{score['technical']}%")
    c3.metric("Behavioral", f"{score['behavioral']}%")

    st.progress(score["overall"] / 100)