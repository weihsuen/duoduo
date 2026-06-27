-- IntervieWhiz.AI — Supabase Postgres schema

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Table 1: job_listings
CREATE TABLE IF NOT EXISTS job_listings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url TEXT,
    company TEXT,
    title TEXT,
    description TEXT,
    keywords JSONB DEFAULT '[]'::jsonb,
    raw_extract JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table 2: interview_sessions
CREATE TABLE IF NOT EXISTS interview_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES job_listings(id) ON DELETE SET NULL,
    questions JSONB DEFAULT '[]'::jsonb,
    answers JSONB DEFAULT '[]'::jsonb,
    feedback TEXT,
    scores JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table 3: resumes
CREATE TABLE IF NOT EXISTS resumes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES job_listings(id) ON DELETE SET NULL,
    content TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table 4: applications
CREATE TABLE IF NOT EXISTS applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES job_listings(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'saved',
    application_date DATE,
    interview_date DATE,
    notes TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (job_id)
);
