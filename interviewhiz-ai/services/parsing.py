import json
import re


def safe_parse_json(text: str) -> dict:
    parsed = parse_json_from_text(text)
    return parsed if isinstance(parsed, dict) else {}


def parse_json_from_text(text: str):
    text = (text or "").strip()
    if not text:
        return None

    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence_match:
        text = fence_match.group(1).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    for start_char, end_char in ("[", "]"), ("{", "}"):
        start = text.find(start_char)
        end = text.rfind(end_char)
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                continue
    return None
