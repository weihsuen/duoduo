import json
from typing import Optional

from dotenv import load_dotenv
from exa_py import Exa
from exa_py.utils import format_exa_result

from services.llm_client import DEFAULT_MODEL, call_llm, get_openai_client, get_secret
from services.parsing import parse_json_from_text
from services.prompts import INTERVIEW_SEARCH_SYSTEM, JOB_EXTRACTION_PROMPT

load_dotenv()

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "exa_search",
            "description": "Perform a search query on the web, and retrieve the most relevant web data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "Search the web for the specified company's website, the interview "
                            "questions asked by the company for the role specified and the interview "
                            "questions that are commonly asked for the role the person is applying for."
                        ),
                    },
                },
                "required": ["query"],
            },
        },
    }
]

MAX_AGENT_ROUNDS = 4
SEARCH_NUM_RESULTS = 5


def _get_exa_client() -> Optional[Exa]:
    api_key = get_secret("EXA_API_KEY")
    if not api_key:
        return None
    return Exa(api_key=api_key)


def _execute_exa_search(query: str, num_results: int = SEARCH_NUM_RESULTS) -> str:
    exa = _get_exa_client()
    if not exa:
        return "Error: EXA_API_KEY is not configured."
    try:
        result = exa.search(query, num_results=num_results)
        if not result.results:
            return f"No results found for query: {query}"
        return format_exa_result(result, max_len=2048)
    except Exception as exc:
        return f"Exa search failed: {exc}"


def run_web_search_agent(
    user_prompt: str,
    system_prompt: Optional[str] = None,
    max_rounds: int = MAX_AGENT_ROUNDS,
) -> str:
    """Run an OpenAI agent loop that can call exa_search and return a final answer."""
    openai_client = get_openai_client()
    if not openai_client:
        return "Error: OPENAI_API_KEY is not configured."

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})

    for _ in range(max_rounds):
        response = openai_client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )
        message = response.choices[0].message

        if not message.tool_calls:
            return message.content or ""

        messages.append(
            {
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "type": tool_call.type,
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        },
                    }
                    for tool_call in message.tool_calls
                ],
            }
        )
        for tool_call in message.tool_calls:
            if tool_call.function.name == "exa_search":
                args = json.loads(tool_call.function.arguments)
                result = _execute_exa_search(args.get("query", ""))
            else:
                result = f"Unknown tool: {tool_call.function.name}"

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                }
            )

    final = openai_client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=messages,
    )
    return final.choices[0].message.content or ""


def extract_job_listing(url: str) -> dict:
    fallback = {
        "url": url or "https://example.com/jobs/placeholder",
        "company": "Example Corp",
        "title": "Software Engineer",
        "description": "Placeholder job description. Wire Exa extraction here.",
        "keywords": ["python", "apis", "teamwork"],
    }
    if not url:
        return fallback

    exa = _get_exa_client()
    if not exa or not get_openai_client():
        return {**fallback, "url": url}

    try:
        contents = exa.get_contents(url)
        if not contents.results:
            return {**fallback, "url": url}

        page_text = contents.results[0].text or ""
        if not page_text.strip():
            return {**fallback, "url": url}

        raw = call_llm(
            JOB_EXTRACTION_PROMPT,
            f"URL: {url}\n\nPage text:\n{page_text[:12000]}",
            temperature=0.1,
        )
        parsed = parse_json_from_text(raw)
        if not isinstance(parsed, dict):
            return {**fallback, "url": url, "description": page_text[:2000]}

        return {
            "url": url,
            "company": parsed.get("company") or fallback["company"],
            "title": parsed.get("title") or fallback["title"],
            "description": parsed.get("description") or page_text[:2000],
            "keywords": parsed.get("keywords") or fallback["keywords"],
        }
    except Exception:
        return {**fallback, "url": url}


def search_interview_info(company: str, role_title: str) -> list:
    fallback = [
        {
            "title": f"{company} interview tips (placeholder)",
            "url": "https://example.com/interview-tips",
        },
        {
            "title": f"{role_title} common questions (placeholder)",
            "url": "https://example.com/questions",
        },
    ]

    if not get_openai_client() or not _get_exa_client():
        return fallback

    prompt = (
        f"Research interview preparation resources for:\n"
        f"- Company: {company}\n"
        f"- Role: {role_title}\n\n"
        f"Find company-specific interview experiences, common questions for this role, "
        f"and reputable prep guides."
    )
    raw = run_web_search_agent(prompt, INTERVIEW_SEARCH_SYSTEM)
    parsed = parse_json_from_text(raw)

    if not isinstance(parsed, list):
        return fallback

    sources = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        title = item.get("title")
        item_url = item.get("url")
        if title and item_url:
            sources.append({"title": str(title), "url": str(item_url)})

    return sources or fallback
