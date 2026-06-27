"""
Supabase client for IntervieWhiz.AI.

This file connects your Streamlit app to the Supabase Postgres tables:

- job_listings
- interview_sessions
- resumes
- applications
"""

import os
from typing import Any, Dict, List, Optional

import streamlit as st
from supabase import Client, create_client


def _get_secret(name: str) -> Optional[str]:
    """
    Reads config from Streamlit secrets first, then environment variables.

    Works with:
    1. .streamlit/secrets.toml
    2. normal environment variables
    """
    try:
        value = st.secrets.get(name)
        if value:
            return value
    except Exception:
        pass

    return os.getenv(name)


def get_supabase_client() -> Client:
    """
    Creates and returns a Supabase client.

    Required config:
    - SUPABASE_URL
    - SUPABASE_KEY
    """
    supabase_url = _get_secret("SUPABASE_URL")
    supabase_key = _get_secret("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        raise RuntimeError(
            "Missing SUPABASE_URL or SUPABASE_KEY. "
            "Add them to .streamlit/secrets.toml or environment variables."
        )

    return create_client(supabase_url, supabase_key)


def _first_row(response: Any) -> Dict[str, Any]:
    """
    Supabase insert/upsert responses usually return data as a list.
    This safely returns the first row.
    """
    if not response.data:
        return {}
    return response.data[0]


def _clean_date(value: Any) -> Optional[str]:
    """
    Supabase DATE columns accept YYYY-MM-DD or null.
    Empty string can cause errors, so convert it to None.
    """
    if value in ("", None):
        return None
    return str(value)


def save_job_listing(job_data: dict) -> dict:
    """
    INSERT into job_listings.

    Expected job_data example:
    {
        "url": "...",
        "company": "...",
        "title": "...",
        "description": "...",
        "keywords": ["Python", "SQL"],
        ...
    }
    """
    supabase = get_supabase_client()

    payload = {
        "url": job_data.get("url"),
        "company": job_data.get("company"),
        "title": job_data.get("title"),
        "description": job_data.get("description"),
        "keywords": job_data.get("keywords", []),
        "raw_extract": job_data,
    }

    response = (
        supabase
        .table("job_listings")
        .insert(payload)
        .execute()
    )

    return _first_row(response)


def get_job_listings() -> list:
    """
    SELECT * FROM job_listings ORDER BY created_at DESC.
    """
    supabase = get_supabase_client()

    response = (
        supabase
        .table("job_listings")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )

    return response.data or []


def save_interview_session(session_data: dict) -> dict:
    """
    INSERT into interview_sessions.

    Expected session_data example:
    {
        "job_id": "...",
        "questions": [...],
        "answers": [...],
        "feedback": "...",
        "scores": {
            "overall": 72,
            "technical": 68,
            "behavioral": 76
        }
    }
    """
    supabase = get_supabase_client()

    payload = {
        "job_id": session_data.get("job_id"),
        "questions": session_data.get("questions", []),
        "answers": session_data.get("answers", []),
        "feedback": session_data.get("feedback"),
        "scores": session_data.get("scores", {}),
    }

    response = (
        supabase
        .table("interview_sessions")
        .insert(payload)
        .execute()
    )

    return _first_row(response)


def save_resume(resume_data: dict) -> dict:
    """
    INSERT into resumes.

    Expected resume_data example:
    {
        "job_id": "...",
        "content": "...",
        "metadata": {...}
    }
    """
    supabase = get_supabase_client()

    payload = {
        "job_id": resume_data.get("job_id"),
        "content": resume_data.get("content"),
        "metadata": resume_data.get("metadata", {}),
    }

    response = (
        supabase
        .table("resumes")
        .insert(payload)
        .execute()
    )

    return _first_row(response)


def get_latest_scores_by_job() -> list:
    """
    Gets the latest interview score for each job_id.

    Returns:
    [
        {
            "job_id": "...",
            "overall": 72,
            "technical": 68,
            "behavioral": 76
        }
    ]
    """
    supabase = get_supabase_client()

    response = (
        supabase
        .table("interview_sessions")
        .select("job_id, scores, created_at")
        .order("created_at", desc=True)
        .execute()
    )

    rows = response.data or []
    seen_job_ids = set()
    latest_scores = []

    for row in rows:
        job_id = row.get("job_id")

        if not job_id or job_id in seen_job_ids:
            continue

        scores = row.get("scores") or {}

        latest_scores.append({
            "job_id": job_id,
            "overall": scores.get("overall", 0),
            "technical": scores.get("technical", 0),
            "behavioral": scores.get("behavioral", 0),
        })

        seen_job_ids.add(job_id)

    return latest_scores


def upsert_application(application_data: dict) -> dict:
    """
    UPSERT into applications.

    Your schema has:
        UNIQUE(job_id)

    So this updates the existing application row if the job_id already exists.
    Otherwise, it inserts a new row.
    """
    supabase = get_supabase_client()

    payload = {
        "job_id": application_data.get("job_id"),
        "status": application_data.get("status", "saved"),
        "application_date": _clean_date(application_data.get("application_date")),
        "interview_date": _clean_date(application_data.get("interview_date")),
        "notes": application_data.get("notes"),
    }

    if not payload["job_id"]:
        raise ValueError("upsert_application requires job_id")

    response = (
        supabase
        .table("applications")
        .upsert(payload, on_conflict="job_id")
        .execute()
    )

    return _first_row(response)


def get_applications() -> list:
    """
    SELECT * FROM applications ORDER BY updated_at DESC.
    """
    supabase = get_supabase_client()

    response = (
        supabase
        .table("applications")
        .select("*")
        .order("updated_at", desc=True)
        .execute()
    )

    return response.data or []