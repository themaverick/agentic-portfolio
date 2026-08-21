-- Enable Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Drop deprecated or existing entity tables to ensure fresh schema migration
DROP TABLE IF EXISTS portfolio_chunks CASCADE;
DROP TABLE IF EXISTS faqs CASCADE;
DROP TABLE IF EXISTS projects CASCADE;
DROP TABLE IF EXISTS experiences CASCADE;
DROP FUNCTION IF EXISTS match_portfolio_hybrid CASCADE;
DROP FUNCTION IF EXISTS match_projects_hybrid CASCADE;
DROP FUNCTION IF EXISTS match_experiences_hybrid CASCADE;
DROP FUNCTION IF EXISTS match_faqs_hybrid CASCADE;

-- 1. Projects Table (Primary Entity + Hybrid Vector Search)
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug VARCHAR(100) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    tagline VARCHAR(500) NOT NULL,
    problem_statement TEXT NOT NULL,
    solution_overview TEXT NOT NULL,
    architecture_metadata JSONB NOT NULL DEFAULT '{}',
    impact_metrics JSONB NOT NULL DEFAULT '[]',
    github_url VARCHAR(500),
    live_demo_url VARCHAR(500),
    is_featured BOOLEAN DEFAULT false,
    display_order INT DEFAULT 0,
    embedding vector(768),
    tsv tsvector GENERATED ALWAYS AS (
        to_tsvector('english', coalesce(title, '') || ' ' || coalesce(tagline, '') || ' ' || coalesce(problem_statement, '') || ' ' || coalesce(solution_overview, ''))
    ) STORED,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Professional Experience Table (Primary Entity + Hybrid Vector Search)
CREATE TABLE IF NOT EXISTS experiences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company VARCHAR(255) NOT NULL,
    role VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    employment_type VARCHAR(50) DEFAULT 'Full-time',
    start_date DATE NOT NULL,
    end_date DATE,
    is_current BOOLEAN GENERATED ALWAYS AS (end_date IS NULL) STORED,
    summary TEXT NOT NULL,
    achievements TEXT[] NOT NULL DEFAULT '{}',
    embedding vector(768),
    tsv tsvector GENERATED ALWAYS AS (
        to_tsvector('english', coalesce(role, '') || ' ' || coalesce(company, '') || ' ' || coalesce(summary, ''))
    ) STORED,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. FAQs & System Rationale Table (Relational Q&A + Hybrid Vector Search)
CREATE TABLE IF NOT EXISTS faqs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    category VARCHAR(50) DEFAULT 'general',
    related_project_slug VARCHAR(100) REFERENCES projects(slug) ON DELETE SET NULL,
    related_company_slug VARCHAR(100),
    embedding vector(768),
    tsv tsvector GENERATED ALWAYS AS (
        to_tsvector('english', coalesce(question, '') || ' ' || coalesce(answer, ''))
    ) STORED,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Legacy System Trade-offs Table (Retained for structured queries)
CREATE TABLE IF NOT EXISTS system_tradeoffs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    topic VARCHAR(255) NOT NULL,
    context_slug VARCHAR(100) NOT NULL,
    decision TEXT NOT NULL,
    alternatives_considered TEXT[] NOT NULL,
    rationale TEXT NOT NULL,
    tradeoffs_accepted TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Skills Taxonomy
CREATE TABLE IF NOT EXISTS skills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(50) NOT NULL,
    proficiency_level VARCHAR(20) DEFAULT 'Advanced'
);

CREATE TABLE IF NOT EXISTS project_skills (
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    skill_id UUID REFERENCES skills(id) ON DELETE CASCADE,
    PRIMARY KEY (project_id, skill_id)
);

-- 6. Recruiter Leads Table
CREATE TABLE IF NOT EXISTS recruiter_leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    recruiter_name VARCHAR(255) NOT NULL,
    company VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    linkedin_url VARCHAR(500),
    message TEXT,
    salary_band VARCHAR(100),
    status VARCHAR(50) DEFAULT 'NEW',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_experiences_dates ON experiences(start_date DESC);
CREATE INDEX IF NOT EXISTS idx_recruiter_leads_status ON recruiter_leads(status, created_at DESC);

-- Vector & Full-Text Search Indexes
CREATE INDEX IF NOT EXISTS idx_projects_hnsw ON projects USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
CREATE INDEX IF NOT EXISTS idx_projects_tsv ON projects USING GIN(tsv);

CREATE INDEX IF NOT EXISTS idx_experiences_hnsw ON experiences USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
CREATE INDEX IF NOT EXISTS idx_experiences_tsv ON experiences USING GIN(tsv);

CREATE INDEX IF NOT EXISTS idx_faqs_hnsw ON faqs USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
CREATE INDEX IF NOT EXISTS idx_faqs_tsv ON faqs USING GIN(tsv);

-- Hybrid Search Stored Procedure: Projects
CREATE OR REPLACE FUNCTION match_projects_hybrid(
    query_text TEXT,
    query_embedding vector(768),
    match_count INT DEFAULT 5,
    rrf_k INT DEFAULT 60
)
RETURNS TABLE (
    id UUID,
    slug VARCHAR(100),
    title VARCHAR(255),
    tagline VARCHAR(500),
    problem_statement TEXT,
    solution_overview TEXT,
    architecture_metadata JSONB,
    impact_metrics JSONB,
    rrf_score FLOAT
)
LANGUAGE sql STABLE AS $$
WITH dense_matches AS (
    SELECT p.id, ROW_NUMBER() OVER (ORDER BY p.embedding <=> query_embedding) AS rank
    FROM projects p
    WHERE p.embedding IS NOT NULL
    ORDER BY p.embedding <=> query_embedding
    LIMIT match_count * 2
),
sparse_matches AS (
    SELECT p.id, ROW_NUMBER() OVER (ORDER BY ts_rank_cd(p.tsv, plainto_tsquery('english', query_text)) DESC) AS rank
    FROM projects p
    WHERE p.tsv @@ plainto_tsquery('english', query_text)
    ORDER BY ts_rank_cd(p.tsv, plainto_tsquery('english', query_text)) DESC
    LIMIT match_count * 2
)
SELECT 
    p.id, p.slug, p.title, p.tagline, p.problem_statement, p.solution_overview, p.architecture_metadata, p.impact_metrics,
    (COALESCE(1.0 / (rrf_k + dm.rank), 0.0) + COALESCE(1.0 / (rrf_k + sm.rank), 0.0))::FLOAT AS rrf_score
FROM projects p
LEFT JOIN dense_matches dm ON p.id = dm.id
LEFT JOIN sparse_matches sm ON p.id = sm.id
WHERE dm.id IS NOT NULL OR sm.id IS NOT NULL
ORDER BY rrf_score DESC
LIMIT match_count;
$$;

-- Hybrid Search Stored Procedure: Experiences
CREATE OR REPLACE FUNCTION match_experiences_hybrid(
    query_text TEXT,
    query_embedding vector(768),
    match_count INT DEFAULT 5,
    rrf_k INT DEFAULT 60
)
RETURNS TABLE (
    id UUID,
    company VARCHAR(255),
    role VARCHAR(255),
    summary TEXT,
    achievements TEXT[],
    rrf_score FLOAT
)
LANGUAGE sql STABLE AS $$
WITH dense_matches AS (
    SELECT e.id, ROW_NUMBER() OVER (ORDER BY e.embedding <=> query_embedding) AS rank
    FROM experiences e
    WHERE e.embedding IS NOT NULL
    ORDER BY e.embedding <=> query_embedding
    LIMIT match_count * 2
),
sparse_matches AS (
    SELECT e.id, ROW_NUMBER() OVER (ORDER BY ts_rank_cd(e.tsv, plainto_tsquery('english', query_text)) DESC) AS rank
    FROM experiences e
    WHERE e.tsv @@ plainto_tsquery('english', query_text)
    ORDER BY ts_rank_cd(e.tsv, plainto_tsquery('english', query_text)) DESC
    LIMIT match_count * 2
)
SELECT 
    e.id, e.company, e.role, e.summary, e.achievements,
    (COALESCE(1.0 / (rrf_k + dm.rank), 0.0) + COALESCE(1.0 / (rrf_k + sm.rank), 0.0))::FLOAT AS rrf_score
FROM experiences e
LEFT JOIN dense_matches dm ON e.id = dm.id
LEFT JOIN sparse_matches sm ON e.id = sm.id
WHERE dm.id IS NOT NULL OR sm.id IS NOT NULL
ORDER BY rrf_score DESC
LIMIT match_count;
$$;

-- Hybrid Search Stored Procedure: FAQs & Tradeoffs
CREATE OR REPLACE FUNCTION match_faqs_hybrid(
    query_text TEXT,
    query_embedding vector(768),
    match_count INT DEFAULT 5,
    rrf_k INT DEFAULT 60
)
RETURNS TABLE (
    id UUID,
    question TEXT,
    answer TEXT,
    category VARCHAR(50),
    related_project_slug VARCHAR(100),
    related_company_slug VARCHAR(100),
    rrf_score FLOAT
)
LANGUAGE sql STABLE AS $$
WITH dense_matches AS (
    SELECT f.id, ROW_NUMBER() OVER (ORDER BY f.embedding <=> query_embedding) AS rank
    FROM faqs f
    WHERE f.embedding IS NOT NULL
    ORDER BY f.embedding <=> query_embedding
    LIMIT match_count * 2
),
sparse_matches AS (
    SELECT f.id, ROW_NUMBER() OVER (ORDER BY ts_rank_cd(f.tsv, plainto_tsquery('english', query_text)) DESC) AS rank
    FROM faqs f
    WHERE f.tsv @@ plainto_tsquery('english', query_text)
    ORDER BY ts_rank_cd(f.tsv, plainto_tsquery('english', query_text)) DESC
    LIMIT match_count * 2
)
SELECT 
    f.id, f.question, f.answer, f.category, f.related_project_slug, f.related_company_slug,
    (COALESCE(1.0 / (rrf_k + dm.rank), 0.0) + COALESCE(1.0 / (rrf_k + sm.rank), 0.0))::FLOAT AS rrf_score
FROM faqs f
LEFT JOIN dense_matches dm ON f.id = dm.id
LEFT JOIN sparse_matches sm ON f.id = sm.id
WHERE dm.id IS NOT NULL OR sm.id IS NOT NULL
ORDER BY rrf_score DESC
LIMIT match_count;
$$;