from services.supabase_client import save_job_listing, get_job_listings


def main():
    print("Testing Supabase insert...")

    saved = save_job_listing({
        "url": "https://example.com/job",
        "company": "Demo Company",
        "title": "Software Engineer",
        "description": "This is a test job listing for Supabase.",
        "keywords": ["Python", "SQL", "Supabase"],
    })

    print("Saved row:")
    print(saved)

    print("\nTesting Supabase select...")
    jobs = get_job_listings()

    print(f"Found {len(jobs)} job listing(s):")
    for job in jobs:
        print(f"- {job.get('company')} | {job.get('title')} | {job.get('id')}")


if __name__ == "__main__":
    main()