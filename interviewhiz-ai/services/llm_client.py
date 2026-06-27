import os
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DEFAULT_MODEL = "gpt-4o-mini"


def get_secret(name: str) -> Optional[str]:
    value = os.getenv(name)
    if value:
        return value
    try:
        import streamlit as st

        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return None


def get_openai_client() -> Optional[OpenAI]:
    api_key = get_secret("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def call_llm(system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
    client = get_openai_client()
    if not client:
        return (
            "Error: OPENAI_API_KEY is not configured. "
            "Add it to .env or .streamlit/secrets.toml."
        )
    if not (user_prompt or "").strip():
        return "No input provided."

    try:
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
        )
        return response.choices[0].message.content or ""
    except Exception as exc:
        return f"LLM request failed: {exc}"