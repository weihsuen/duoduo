from services.llm_client import call_llm
from services.parsing import safe_parse_json
from services.prompts import SCORING_PROMPT


def calculate_dummy_score() -> dict:
    return {"overall": 65, "technical": 60, "behavioral": 70}


def calculate_score(qa_text: str) -> dict:
    fallback = calculate_dummy_score()
    if not (qa_text or "").strip():
        return fallback

    raw = call_llm(SCORING_PROMPT, qa_text, temperature=0.1)
    parsed = safe_parse_json(raw)
    if not parsed:
        return fallback

    def clamp(value) -> int:
        try:
            return max(0, min(100, int(value)))
        except (TypeError, ValueError):
            return fallback["overall"]

    return {
        "overall": clamp(parsed.get("overall")),
        "technical": clamp(parsed.get("technical")),
        "behavioral": clamp(parsed.get("behavioral")),
    }
