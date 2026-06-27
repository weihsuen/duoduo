from datetime import datetime
import os

import streamlit as st
from supabase import create_client


@st.cache_resource
def get_supabase_client():
    url = (
        st.secrets.get("SUPABASE_URL")
        or os.getenv("SUPABASE_URL")
    )

    key = (
        st.secrets.get("SUPABASE_KEY")
        or st.secrets.get("SUPABASE_ANON_KEY")
        or os.getenv("SUPABASE_KEY")
        or os.getenv("SUPABASE_ANON_KEY")
    )

    if not url or not key:
        raise RuntimeError(
            "Missing SUPABASE_URL or SUPABASE_KEY. "
            "Add them to .streamlit/secrets.toml or environment variables."
        )

    return create_client(url, key)


# ---------------------------------------------------------------------
# Job listings
# ---------------------------------------------------------------------

def get_job_listings():
    supabase = get_supabase_client()

    response = (
        supabase
        .table("job_listings")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )

    return response.data or []


# ---------------------------------------------------------------------
# Applications dashboard
# ---------------------------------------------------------------------

def get_applications():
    supabase = get_supabase_client()

    response = (
        supabase
        .table("applications")
        .select("*")
        .order("updated_at", desc=True)
        .execute()
    )

    return response.data or []


def upsert_application(payload):
    supabase = get_supabase_client()

    payload["updated_at"] = datetime.utcnow().isoformat()

    response = (
        supabase
        .table("applications")
        .upsert(payload, on_conflict="job_id")
        .execute()
    )

    return response.data


def get_latest_scores_by_job():
    supabase = get_supabase_client()

    response = (
        supabase
        .table("interview_sessions")
        .select("job_id, scores, created_at")
        .order("created_at", desc=True)
        .execute()
    )

    sessions = response.data or []

    latest_by_job = {}

    for session in sessions:
        job_id = session.get("job_id")

        if not job_id:
            continue

        if job_id in latest_by_job:
            continue

        scores = session.get("scores") or {}

        latest_by_job[job_id] = {
            "job_id": job_id,
            "overall": scores.get("overall"),
            "scores": scores,
            "created_at": session.get("created_at"),
        }

    return list(latest_by_job.values())


# ---------------------------------------------------------------------
# Resume item bank
# Stores reusable projects, achievements, experience, leadership, etc.
# ---------------------------------------------------------------------

def get_resume_items():
    supabase = get_supabase_client()

    response = (
        supabase
        .table("resume_items")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )

    return response.data or []


def upsert_resume_item(payload):
    """
    Insert or update a resume-bank item.

    Expected payload:
    {
        "id": optional UUID,
        "item_type": "Project" / "Achievement" / etc,
        "title": "...",
        "organization": "...",
        "date_range": "...",
        "skills": "...",
        "description": "...",
        "metadata": optional dict
    }
    """
    supabase = get_supabase_client()

    item_id = payload.get("id")

    clean_payload = {
        "item_type": payload.get("item_type") or "Project",
        "title": payload.get("title"),
        "organization": payload.get("organization"),
        "date_range": payload.get("date_range"),
        "skills": payload.get("skills"),
        "description": payload.get("description"),
        "metadata": payload.get("metadata") or {},
        "updated_at": datetime.utcnow().isoformat(),
    }

    if item_id:
        response = (
            supabase
            .table("resume_items")
            .update(clean_payload)
            .eq("id", item_id)
            .execute()
        )
    else:
        clean_payload["created_at"] = datetime.utcnow().isoformat()

        response = (
            supabase
            .table("resume_items")
            .insert(clean_payload)
            .execute()
        )

    return response.data


def delete_resume_item(item_id):
    supabase = get_supabase_client()

    response = (
        supabase
        .table("resume_items")
        .delete()
        .eq("id", item_id)
        .execute()
    )

    return response.data


# ---------------------------------------------------------------------
# Generated resumes
# Uses your existing `resumes` table:
# id UUID, job_id UUID, content TEXT, metadata JSONB, created_at TIMESTAMPTZ
# ---------------------------------------------------------------------

def save_resume(payload):
    """
    Save generated tailored resume.

    Expected payload:
    {
        "job_id": selected job UUID,
        "content": generated resume markdown,
        "metadata": optional dict
    }
    """
    supabase = get_supabase_client()

    clean_payload = {
        "job_id": payload.get("job_id"),
        "content": payload.get("content"),
        "metadata": payload.get("metadata") or {},
        "created_at": payload.get("created_at") or datetime.utcnow().isoformat(),
    }

    response = (
        supabase
        .table("resumes")
        .insert(clean_payload)
        .execute()
    )

    return response.data


def get_resumes():
    supabase = get_supabase_client()

    response = (
        supabase
        .table("resumes")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )

    return response.data or []


def get_resumes_by_job(job_id):
    supabase = get_supabase_client()

    response = (
        supabase
        .table("resumes")
        .select("*")
        .eq("job_id", job_id)
        .order("created_at", desc=True)
        .execute()
    )

    return response.data or []