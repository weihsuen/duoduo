"""Placeholder Exa API client. No real API calls yet."""


def extract_job_listing(url: str) -> dict:
    # TODO: Call Exa to scrape/extract job listing from URL
    return {
        "url": url or "https://example.com/jobs/placeholder",
        "company": "Example Corp",
        "title": "Software Engineer",
        "description": "Placeholder job description. Wire Exa extraction here.",
        "keywords": ["python", "apis", "teamwork"],
    }


def search_interview_info(company: str, role_title: str) -> list:
    # TODO: Call Exa search for interview tips, Glassdoor-style sources, etc.
    return [
        {"title": f"{company} interview tips (placeholder)", "url": "https://example.com/interview-tips"},
        {"title": f"{role_title} common questions (placeholder)", "url": "https://example.com/questions"},
    ]
