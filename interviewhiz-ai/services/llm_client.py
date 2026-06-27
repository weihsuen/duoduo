"""Placeholder OpenAI client. No real API calls yet."""


def call_llm(system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
    # TODO: Integrate OpenAI API (chat completions) using OPENAI_API_KEY from secrets
    _ = (system_prompt, user_prompt, temperature)
    return "Placeholder LLM response. Replace with OpenAI integration."
