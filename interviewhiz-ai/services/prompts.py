JOB_ANALYSIS_PROMPT = """Analyze the job listing. Extract required skills, responsibilities, and seniority level.
Return structured insights for interview preparation."""

INTERVIEW_QUESTION_PROMPT = """Generate 5 interview questions tailored to this job listing.
Mix behavioral and technical questions."""

INTERVIEW_FEEDBACK_PROMPT = """Review the candidate's answers. Give concise, actionable feedback
on clarity, relevance, and areas to improve."""

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
