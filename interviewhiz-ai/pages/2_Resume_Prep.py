import streamlit as st

from services.llm_client import call_llm
from services.prompts import RESUME_GENERATION_PROMPT
from services.supabase_client import get_job_listings, save_resume

st.set_page_config(page_title="Resume Prep", page_icon="📄", layout="wide")
st.title("Resume Prep")

jobs = get_job_listings()
job_options = {j.get("title", f"Job {j.get('id', '?')}"): j for j in jobs}
labels = list(job_options.keys()) or ["(No saved jobs — placeholder)"]

selected_label = st.selectbox("Saved job listing", labels)
selected_job = job_options.get(selected_label, {})

experience_bank = st.text_area(
    "Project / work experience bank",
    height=200,
    placeholder="Paste bullets about projects, roles, and achievements.",
)

if st.button("Generate Tailored Resume", use_container_width=True):
    prompt_input = f"Job: {selected_job}\n\nExperience:\n{experience_bank}"
    resume_md = call_llm(RESUME_GENERATION_PROMPT, prompt_input)
    st.session_state.generated_resume = resume_md
    save_resume({"job_id": selected_job.get("id"), "content": resume_md})

st.subheader("Tailored resume preview")
resume_content = st.session_state.get(
    "generated_resume",
    "## Your Name\n\n*Generated resume will appear here.*\n\n- Placeholder bullet one\n- Placeholder bullet two",
)
st.markdown(resume_content)

st.download_button(
    label="Download resume (placeholder)",
    data=resume_content,
    file_name="tailored_resume.md",
    mime="text/markdown",
)
