JOB_ANALYSIS_PROMPT = """Analyze the job listing for interview preparation.
Return ONLY valid JSON (no markdown fences) with keys:
- skills: array of required skill strings
- responsibilities: array of key responsibility strings
- seniority: string (e.g. junior, mid, senior)
- summary: one-paragraph overview for the candidate"""

INTERVIEW_QUESTION_PROMPT = """Generate exactly 10 interview questions tailored to this job listing.
Mix behavioral and technical questions.
Return one question per line, numbered 1-10. No extra commentary."""

INTERVIEW_FEEDBACK_PROMPT = """Review the candidate's interview practice answers.
Give concise, actionable feedback on clarity, relevance, and areas to improve.
Use short sections with bullet points where helpful."""

SCORING_PROMPT = """Score the candidate's interview practice answers.
Return ONLY valid JSON (no markdown fences) with integer keys 0-100:
- overall
- technical
- behavioral"""

RESUME_GENERATION_PROMPT = """Generate a tailored resume in markdown from the candidate's experience bank
and the target job requirements. Emphasize matching skills.
Use clear sections: Summary, Skills, Experience, Projects, Education (if inferable)."""

JOB_EXTRACTION_PROMPT = """Extract structured job listing data from raw page text.
Return ONLY valid JSON (no markdown fences) with keys:
company, title, description, keywords (array of skill strings)."""

INTERVIEW_SEARCH_SYSTEM = """You are an interview research assistant.
Use the exa_search tool to find real web sources about company interview processes,
Glassdoor-style reviews, and common questions for the role.

When you have enough information, respond with ONLY a JSON array (no markdown fences):
[{"title": "Source title", "url": "https://..."}, ...]

Include 5-8 high-quality, distinct sources with real URLs from search results."""
