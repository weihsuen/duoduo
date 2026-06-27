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