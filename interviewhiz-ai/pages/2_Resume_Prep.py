import json
from datetime import datetime

import streamlit as st

from services.llm_client import call_llm
from services.prompts import RESUME_GENERATION_PROMPT
from services.supabase_client import (
    delete_resume_item,
    get_job_listings,
    get_resume_items,
    save_resume,
    upsert_resume_item,
)


st.set_page_config(page_title="Resume Prep", page_icon="📄", layout="wide")
st.title("Resume Prep")


def rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()


def format_job_label(job):
    title = job.get("title") or "Untitled role"
    company = job.get("company") or "Unknown company"
    return f"{title} — {company}"


def format_item_label(item):
    item_type = item.get("item_type", "Item")
    title = item.get("title", "Untitled")
    return f"{item_type}: {title}"


def clean_resume_markdown(text):
    if not text:
        return ""

    cleaned = text.strip()

    if cleaned.startswith("```markdown"):
        cleaned = cleaned.removeprefix("```markdown").strip()

    if cleaned.startswith("```md"):
        cleaned = cleaned.removeprefix("```md").strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```").strip()

    if cleaned.endswith("```"):
        cleaned = cleaned.removesuffix("```").strip()

    return cleaned.strip()


def extract_job_keywords(job):
    value = job.get("keywords")

    if not value:
        return ""

    if isinstance(value, list):
        return ", ".join(str(v) for v in value)

    if isinstance(value, dict):
        return json.dumps(value, indent=2)

    return str(value)


def item_to_resume_bank_text(item):
    parts = [
        f"Type: {item.get('item_type', '')}",
        f"Title: {item.get('title', '')}",
        f"Organization: {item.get('organization', '')}",
        f"Date range: {item.get('date_range', '')}",
        f"Skills: {item.get('skills', '')}",
        f"Description / achievements:\n{item.get('description', '')}",
    ]

    return "\n".join([p for p in parts if p and not p.endswith(": ")])


@st.cache_data(ttl=10)
def load_jobs():
    return get_job_listings()


@st.cache_data(ttl=10)
def load_resume_items():
    return get_resume_items()


# ---------------------------------------------------------------------
# 1. Select job
# ---------------------------------------------------------------------

st.subheader("1. Select target job")

jobs = load_jobs()

if not jobs:
    st.warning("No saved job listings found. Add a job listing first.")
    selected_job = None
else:
    selected_index = st.selectbox(
        "Saved job listing",
        options=list(range(len(jobs))),
        format_func=lambda i: format_job_label(jobs[i]),
    )

    selected_job = jobs[selected_index]
    job_keywords = extract_job_keywords(selected_job)

    company = selected_job.get("company") or "Unknown company"
    title = selected_job.get("title") or "Untitled role"
    description = selected_job.get("description") or "No job description saved."

    st.markdown("### Selected job")
    st.markdown(f"**Role:** {title}")
    st.markdown(f"**Company:** {company}")

    if job_keywords:
        st.markdown("**Saved keywords:**")
        st.write(job_keywords)
    else:
        st.info("No saved keywords found for this job.")

    with st.expander("View job description", expanded=False):
        st.write(description)


# ---------------------------------------------------------------------
# 2. Add resume bank item
# ---------------------------------------------------------------------

st.divider()
st.subheader("2. Add projects, work experience, achievements, or activities")

with st.form("add_resume_item_form", clear_on_submit=True):
    col1, col2 = st.columns(2)

    with col1:
        item_type = st.selectbox(
            "Item type",
            [
                "Profile",
                "Education",
                "Technical Skills",
                "Project",
                "Work Experience",
                "Achievement",
                "Leadership",
                "Volunteer Work",
                "Other",
            ],
        )

        title = st.text_input(
            "Title",
            placeholder="e.g. Dataset-Aware Financial Forecasting FYP",
        )

        organization = st.text_input(
            "Organization / context",
            placeholder="e.g. NTU, A*STAR, Hackathon, Internship",
        )

    with col2:
        date_range = st.text_input(
            "Date range",
            placeholder="e.g. Aug 2025 – May 2026",
        )

        skills = st.text_input(
            "Skills / keywords",
            placeholder="e.g. Python, Streamlit, Supabase, forecasting, ML",
        )

    description = st.text_area(
        "Description / achievement bullets",
        height=160,
        placeholder=(
            "Write raw facts here. Example:\n"
            "- Benchmarked 5 time-series foundation models across 139 financial datasets\n"
            "- Built meta-model for model selection with 61% top-1 accuracy\n"
            "- Presented results to academic and A*STAR supervisors\n\n"
            "For personal details, choose item type 'Profile' and add name, email, LinkedIn, GitHub, etc."
        ),
    )

    add_submitted = st.form_submit_button("Save item", use_container_width=True)

    if add_submitted:
        if not title.strip():
            st.error("Title is required.")
        elif not description.strip():
            st.error("Description is required.")
        else:
            upsert_resume_item(
                {
                    "item_type": item_type,
                    "title": title.strip(),
                    "organization": organization.strip(),
                    "date_range": date_range.strip(),
                    "skills": skills.strip(),
                    "description": description.strip(),
                }
            )

            load_resume_items.clear()
            st.success("Saved.")
            rerun()


# ---------------------------------------------------------------------
# 3. Display and edit resume bank
# ---------------------------------------------------------------------

st.divider()
st.subheader("3. Saved resume bank")

resume_items = load_resume_items()

if not resume_items:
    st.info("No saved projects, achievements, or experience items yet.")
else:
    st.caption(
        "All saved items will be given to the LLM. It will decide which ones are relevant for the selected job."
    )

    for item in resume_items:
        item_id = item.get("id")

        with st.expander(format_item_label(item), expanded=False):
            st.markdown(f"**Type:** {item.get('item_type') or 'Item'}")
            st.markdown(f"**Title:** {item.get('title') or 'Untitled'}")

            if item.get("organization"):
                st.markdown(f"**Organization:** {item.get('organization')}")

            if item.get("date_range"):
                st.markdown(f"**Date range:** {item.get('date_range')}")

            if item.get("skills"):
                st.markdown(f"**Skills:** {item.get('skills')}")

            st.markdown("**Description / achievements:**")
            st.write(item.get("description") or "")

            with st.form(f"edit_resume_item_{item_id}"):
                st.markdown("#### Edit item")

                col1, col2 = st.columns(2)

                allowed_types = [
                    "Profile",
                    "Education",
                    "Technical Skills",
                    "Project",
                    "Work Experience",
                    "Achievement",
                    "Leadership",
                    "Volunteer Work",
                    "Other",
                ]

                current_type = item.get("item_type") or "Project"

                with col1:
                    edited_type = st.selectbox(
                        "Item type",
                        allowed_types,
                        index=allowed_types.index(current_type)
                        if current_type in allowed_types
                        else 0,
                        key=f"type_{item_id}",
                    )

                    edited_title = st.text_input(
                        "Title",
                        value=item.get("title") or "",
                        key=f"title_{item_id}",
                    )

                    edited_org = st.text_input(
                        "Organization / context",
                        value=item.get("organization") or "",
                        key=f"org_{item_id}",
                    )

                with col2:
                    edited_date_range = st.text_input(
                        "Date range",
                        value=item.get("date_range") or "",
                        key=f"date_{item_id}",
                    )

                    edited_skills = st.text_input(
                        "Skills / keywords",
                        value=item.get("skills") or "",
                        key=f"skills_{item_id}",
                    )

                edited_description = st.text_area(
                    "Description / achievement bullets",
                    value=item.get("description") or "",
                    height=150,
                    key=f"description_{item_id}",
                )

                col_update, col_delete = st.columns(2)

                update_clicked = col_update.form_submit_button(
                    "Update item",
                    use_container_width=True,
                )

                delete_clicked = col_delete.form_submit_button(
                    "Delete item",
                    use_container_width=True,
                )

                if update_clicked:
                    if not edited_title.strip():
                        st.error("Title is required.")
                    elif not edited_description.strip():
                        st.error("Description is required.")
                    else:
                        upsert_resume_item(
                            {
                                "id": item_id,
                                "item_type": edited_type,
                                "title": edited_title.strip(),
                                "organization": edited_org.strip(),
                                "date_range": edited_date_range.strip(),
                                "skills": edited_skills.strip(),
                                "description": edited_description.strip(),
                            }
                        )

                        load_resume_items.clear()
                        st.success("Updated.")
                        rerun()

                if delete_clicked:
                    delete_resume_item(item_id)
                    load_resume_items.clear()
                    st.success("Deleted.")
                    rerun()


# ---------------------------------------------------------------------
# 4. Generate tailored resume
# ---------------------------------------------------------------------

st.divider()
st.subheader("4. Generate tailored resume")

if resume_items:
    st.info(
        f"{len(resume_items)} saved resume-bank item(s) will be analysed. "
        "The LLM will choose the most relevant ones automatically."
    )

extra_notes = st.text_area(
    "Extra instructions for the resume",
    height=100,
    placeholder=(
        "Optional. Example: Keep it one page, emphasize backend engineering, "
        "make bullets more impact-driven, avoid overclaiming."
    ),
)

generate_disabled = selected_job is None or not resume_items

if st.button(
    "Generate Tailored Resume",
    use_container_width=True,
    disabled=generate_disabled,
):
    job_keywords = extract_job_keywords(selected_job)

    full_resume_bank = "\n\n---\n\n".join(
        item_to_resume_bank_text(item) for item in resume_items
    )

    prompt_input = f"""
Target job title:
{selected_job.get("title")}

Target company:
{selected_job.get("company")}

Target job description:
{selected_job.get("description")}

Saved job keywords:
{job_keywords}

Candidate's complete saved resume bank:
{full_resume_bank}

Extra user instructions:
{extra_notes}

Generate a polished, job-tailored resume.

Hard requirements:
- Return a finished resume, not a template.
- Do not include placeholders like [Your Name], [Your Email], [City], [LinkedIn], [Phone Number], or [University].
- Do not invent missing personal details.
- Do not invent companies, dates, degrees, metrics, tools, awards, or responsibilities.
- If name, contact details, GitHub, LinkedIn, education, or dates are not provided, omit them.
- Do not include an Objective section.
- Use a Summary section only if there is enough evidence from the resume bank.
- Select only the strongest and most relevant items for the target job.
- Do not include every saved item unless all are genuinely relevant.
- Prioritize alignment with the job description and saved keywords.
- Write like a real resume submitted to an employer.
- Return only clean Markdown.
- Do not wrap the output in a code block.

Resume formatting:
- Use Markdown headings.
- Use compact sections.
- Use bullet points, not paragraphs.
- Use 2 to 4 bullets per selected role/project.
- Keep bullets concise and impact-oriented.
- Each bullet should start with a strong action verb.
- Use measurable impact only when the source data supports it.
- Avoid vague filler phrases such as hardworking, passionate, responsible, detail-oriented, and team player.

Preferred structure:
# Candidate Name
Only include this if the name is provided.

Contact line:
Only include if contact details are provided.

## Summary
2 to 3 lines maximum. Omit if there is not enough evidence.

## Technical Skills
Group skills into categories if possible.

## Experience
Use for internships, jobs, or substantial work experience.

## Projects
Use for technical projects, academic projects, hackathons, or portfolio work.

## Education
Only include if education details are provided.

## Leadership, Volunteering & Achievements
Only include relevant items.
"""

    with st.spinner("Generating tailored resume..."):
        resume_md = call_llm(RESUME_GENERATION_PROMPT, prompt_input)

    resume_md = clean_resume_markdown(resume_md)

    st.session_state.generated_resume = resume_md

    save_resume(
        {
            "job_id": selected_job.get("id"),
            "content": resume_md,
            "metadata": {
                "source": "resume_prep",
                "job_title": selected_job.get("title"),
                "company": selected_job.get("company"),
                "keywords": selected_job.get("keywords"),
                "resume_item_count": len(resume_items),
                "generated_at": datetime.utcnow().isoformat(),
            },
        }
    )

    st.success("Resume generated and saved.")


# ---------------------------------------------------------------------
# 5. Resume preview and download
# ---------------------------------------------------------------------

st.divider()
st.subheader("Tailored resume preview")

resume_content = st.session_state.get(
    "generated_resume",
    "Generated resume will appear here after you select a job and click generate.",
)

resume_content = clean_resume_markdown(resume_content)

st.markdown(resume_content)

st.download_button(
    label="Download resume",
    data=resume_content,
    file_name="tailored_resume.md",
    mime="text/markdown",
    use_container_width=True,
)