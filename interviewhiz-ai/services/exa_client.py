import json
from typing import Optional

from dotenv import load_dotenv
from exa_py import Exa
from exa_py.utils import format_exa_result

from services.llm_client import (
    DEFAULT_MODEL,
    call_llm,
    get_openai_client,
    get_secret,
)
from services.parsing import parse_json_from_text
from services.prompts import (
    INTERVIEW_SEARCH_SYSTEM,
    JOB_EXTRACTION_PROMPT,
)

load_dotenv()

SEARCH_NUM_RESULTS = 5
MAX_AGENT_ROUNDS = 4


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "exa_search",
            "description": "Search the web for interview preparation information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                    }
                },
                "required": ["query"],
            },
        },
    }
]


def _get_exa_client() -> Optional[Exa]:
    api_key = get_secret("EXA_API_KEY")

    if not api_key:
        return None

    return Exa(api_key=api_key)


def _looks_like_invalid_job_page(
    original_url: str,
    returned_url: str,
    page_text: str,
) -> bool:

    redirected = (
        returned_url.rstrip("/")
        != original_url.rstrip("/")
    )

    lower = page_text.lower()

    invalid_markers = [
        "no longer available",
        "role no longer available",
        "job expired",
        "position filled",
        "job not found",
        "this posting is closed",
        "404",
        "page not found",
        "access denied",
        "login",
        "sign in",
    ]

    invalid_content = any(
        marker in lower
        for marker in invalid_markers
    )

    redirect_markers = [
        "/search",
        "/jobs",
        "/careers",
        "/login",
        "/signin",
    ]

    suspicious_redirect = (
        redirected
        and any(
            marker in returned_url.lower()
            for marker in redirect_markers
        )
        and len(page_text) < 500
    )

    return invalid_content or suspicious_redirect

def extract_job_listing(
    url: str,
) -> dict:

    empty = {
        "url": url,
        "company": "",
        "title": "",
        "description": "",
        "keywords": [],
        "manual_input_required": False,
    }

    if not url:
        return empty

    exa = _get_exa_client()

    if not exa:
        return {
            **empty,
            "manual_input_required": True,
            "error": "EXA_API_KEY missing",
        }

    if not get_openai_client():
        return {
            **empty,
            "manual_input_required": True,
            "error": "OPENAI_API_KEY missing",
        }

    try:

        contents = exa.get_contents(url)

        if not contents.results:
            raise Exception(
                "No content returned"
            )

        result = contents.results[0]

        returned_url = getattr(
            result,
            "url",
            url,
        )

        page_text = (
            result.text
            or ""
        ).strip()

        print(
            f"[EXTRACT] requested={url}"
        )

        print(
            f"[EXTRACT] returned={returned_url}"
        )

        if (
            not page_text
            or _looks_like_invalid_job_page(
                url,
                returned_url,
                page_text,
            )
        ):

            return {
                **empty,
                "manual_input_required": True,
                "error": (
                    "Unable to access this job posting. "
                    "Please paste the job description manually."
                ),
            }

        raw = call_llm(
            JOB_EXTRACTION_PROMPT,
            f"""
            URL:
            {url}

            JOB CONTENT:
            {page_text[:12000]}
            """,
            temperature=0.1,
        )

        parsed = parse_json_from_text(raw)

        if not isinstance(
            parsed,
            dict,
        ):

            raise Exception(
                "Could not parse extracted job"
            )

        return {
            "url": url,
            "company": parsed.get(
                "company",
                "",
            ),
            "title": parsed.get(
                "title",
                "",
            ),
            "description": parsed.get(
                "description",
                page_text[:3000],
            ),
            "keywords": parsed.get(
                "keywords",
                [],
            ),
            "manual_input_required": False,
        }

    except Exception as exc:

        print(
            "[EXTRACT ERROR]",
            exc,
        )

        return {
            **empty,
            "manual_input_required": True,
            "error": (
                "Could not extract this listing. "
                "Paste the job description manually."
            ),
        }


def _execute_exa_search(
    query: str,
    num_results: int = SEARCH_NUM_RESULTS,
) -> str:

    exa = _get_exa_client()

    if not exa:
        return ""

    try:

        result = exa.search(
            query,
            num_results=num_results,
        )

        if not result.results:
            return ""

        return format_exa_result(
            result,
            max_len=2048,
        )

    except Exception:
        return ""


def run_web_search_agent(
    user_prompt: str,
    system_prompt: Optional[str] = None,
    max_rounds: int = MAX_AGENT_ROUNDS,
) -> str:

    client = get_openai_client()

    if not client:
        return ""

    messages = []

    if system_prompt:
        messages.append(
            {
                "role": "system",
                "content": system_prompt,
            }
        )

    messages.append(
        {
            "role": "user",
            "content": user_prompt,
        }
    )

    for _ in range(max_rounds):

        response = (
            client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
            )
        )

        message = (
            response
            .choices[0]
            .message
        )

        if not message.tool_calls:
            return (
                message.content
                or ""
            )

        messages.append(
            message
        )

        for call in message.tool_calls:

            result = (
                _execute_exa_search(
                    json.loads(
                        call.function.arguments
                    )["query"]
                )
            )

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": result,
                }
            )

    return ""


def search_interview_info(
    company: str,
    role_title: str,
) -> list:

    if (
        not company
        or not role_title
    ):
        return []

    prompt = f"""
Research interview preparation resources.

Company:
{company}

Role:
{role_title}

Return interview experiences,
common questions,
and preparation guides.
"""

    raw = run_web_search_agent(
        prompt,
        INTERVIEW_SEARCH_SYSTEM,
    )

    parsed = parse_json_from_text(
        raw
    )

    if not isinstance(
        parsed,
        list,
    ):
        return []

    return [
        x
        for x in parsed
        if isinstance(
            x,
            dict,
        )
        and x.get("title")
        and x.get("url")
    ]