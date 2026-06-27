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

# RESUME_GENERATION_PROMPT = """Generate a tailored resume in markdown from the candidate's experience bank
# and the target job requirements. Emphasize matching skills.
# Use clear sections: Summary, Skills, Experience, Projects, Education (if inferable)."""

JOB_EXTRACTION_PROMPT = """Extract structured job listing data from raw page text.
Return ONLY valid JSON (no markdown fences) with keys:
company, title, description, keywords (array of skill strings)."""

INTERVIEW_SEARCH_SYSTEM = """You are an interview research assistant.
Use the exa_search tool to find real web sources about company interview processes,
Glassdoor-style reviews, and common questions for the role.

When you have enough information, respond with ONLY a JSON array (no markdown fences):
[{"title": "Source title", "url": "https://..."}, ...]

Include 8-10 high-quality, distinct sources with real URLs from search results."""

RESUME_GENERATION_PROMPT = """
You are an expert technical resume writer.

Your task is to generate a polished, realistic, ATS-friendly resume tailored to a target job.

Critical rules:
- Do NOT return a resume template.
- Do NOT include placeholders such as [Your Name], [Your Email], [City], [LinkedIn], etc.
- Do NOT invent missing personal details.
- Do NOT invent companies, dates, degrees, awards, metrics, tools, or responsibilities.
- Use only information provided in the candidate resume bank and user instructions.
- If contact details are missing, omit the contact line completely.
- If education details are missing, omit the education section completely.
- If a section has no useful content, omit that section.
- Do NOT use an "Objective" section.
- Prefer a concise "Summary" section only if there is enough evidence from the candidate data.
- Return only the resume content in Markdown.
- Do NOT wrap the output in ```markdown or any code block.

Resume structure:
1. Name / Header, only if provided by the user.
2. Short professional summary, 2-3 lines max.
3. Technical Skills, grouped if possible.
4. Experience and Projects, using the most relevant saved items.
5. Education, only if provided.
6. Leadership / Volunteering / Achievements, only if relevant.

Bullet rules:
- Use 2-4 bullets per selected item.
- Each bullet should start with a strong action verb.
- Each bullet should be specific and relevant to the target job.
- Use measurable impact only when the source data provides it.
- Do not force fake metrics.
- Prioritize job keywords naturally.
- Avoid vague phrases like "hardworking", "passionate", "detail-oriented", "team player".
- Keep tone professional and concise.

Formatting rules:
- Use Markdown headings.
- Use clear section names.
- Use bullet points.
- Keep the resume compact.
- Avoid long paragraphs.
"""
