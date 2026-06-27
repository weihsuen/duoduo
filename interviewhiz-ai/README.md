# IntervieWhiz.AI

Hackathon MVP for interview prep, tailored resumes, and job application tracking.

Built with **Streamlit**, **Supabase Postgres**, **Exa** (job extraction & research), and **OpenAI** (LLM). API integrations are placeholders for now.

## Setup

1. Clone the repo and enter the project folder:

   ```bash
   cd interviewhiz-ai
   ```

2. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   # source .venv/bin/activate  # macOS/Linux
   pip install -r requirements.txt
   ```

3. Copy secrets example (optional for local skeleton — app runs without real keys):

   ```bash
   copy .streamlit\secrets.toml.example .streamlit\secrets.toml   # Windows
   # cp .streamlit/secrets.toml.example .streamlit/secrets.toml     # macOS/Linux
   ```

   Edit `.streamlit/secrets.toml` with your keys when ready.

## Run locally

From the `interviewhiz-ai` folder:

```bash
streamlit run app.py
```

Open the URL shown in the terminal (usually http://localhost:8501).

## Supabase tables

1. Create a project at [supabase.com](https://supabase.com).
2. Open **SQL Editor** in the Supabase dashboard.
3. Paste and run the contents of `db/schema.sql`.
4. Add `SUPABASE_URL` and `SUPABASE_KEY` to `.streamlit/secrets.toml`.

## Secrets

| Key | Purpose |
|-----|---------|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_KEY` | Supabase anon/service key |
| `EXA_API_KEY` | Exa job extraction & search |
| `OPENAI_API_KEY` | LLM analysis, questions, feedback, resumes |

Never commit `.streamlit/secrets.toml` — it is listed in `.gitignore`.

## Deploy (Zo Computer)

1. Push the repo to GitHub.
2. Connect the repo on [Zo Computer](https://zocomputer.com) (or another Streamlit host).
3. Set the start command: `streamlit run app.py`
4. Add the same secrets in the host's environment or secrets UI.

## Project layout

```
interviewhiz-ai/
├── app.py                 # Home page
├── pages/                 # Streamlit multipage app
├── services/              # API & DB placeholders
├── db/schema.sql          # Postgres schema
├── .streamlit/            # Streamlit config & secrets
└── requirements.txt
```

## Next implementation steps

1. **`services/supabase_client.py`** — wire real Supabase CRUD against `db/schema.sql`
2. **`services/exa_client.py`** — implement job extraction and interview research
3. **`services/llm_client.py`** — OpenAI chat completions with prompts from `services/prompts.py`
4. **`services/scoring.py`** — replace dummy scores with LLM-based or rule-based scoring
5. **Interview Prep page** — persist sessions via `save_interview_session`

## Testing

Tests are not set up yet.
