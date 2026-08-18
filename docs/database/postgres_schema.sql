-- Enable Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- 1. Projects Table
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
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Professional Experience Table
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
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. System Trade-offs Table
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

-- 4. Skills Taxonomy
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

-- 5. Recruiter Leads Table
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

-- 6. Knowledge Chunks Table (Dense Vector + Full-Text Search)
CREATE TABLE IF NOT EXISTS portfolio_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID,
    slug VARCHAR(100),
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    embedding vector(768) NOT NULL,
    tsv tsvector GENERATED ALWAYS AS (
        to_tsvector('english', coalesce(title, '') || ' ' || coalesce(content, ''))
    ) STORED,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_experiences_dates ON experiences(start_date DESC);
CREATE INDEX IF NOT EXISTS idx_recruiter_leads_status ON recruiter_leads(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_portfolio_chunks_hnsw ON portfolio_chunks USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
CREATE INDEX IF NOT EXISTS idx_portfolio_chunks_tsv ON portfolio_chunks USING GIN(tsv);

-- Hybrid Search Stored Procedure (Reciprocal Rank Fusion)
CREATE OR REPLACE FUNCTION match_portfolio_hybrid(
    query_text TEXT,
    query_embedding vector(768),
    match_count INT DEFAULT 5,
    rrf_k INT DEFAULT 60
)
RETURNS TABLE (
    id UUID,
    entity_type VARCHAR(50),
    title VARCHAR(255),
    content TEXT,
    metadata JSONB,
    dense_rank BIGINT,
    sparse_rank BIGINT,
    rrf_score FLOAT
)
LANGUAGE sql STABLE AS $$ WITH dense_matches AS (     SELECT pc.id, ROW_NUMBER() OVER (ORDER BY pc.embedding <=> query_embedding) AS rank     FROM portfolio_chunks pc     ORDER BY pc.embedding <=> query_embedding     LIMIT match_count * 2 ), sparse_matches AS (     SELECT pc.id, ROW_NUMBER() OVER (ORDER BY ts_rank_cd(pc.tsv, plainto_tsquery('english', query_text)) DESC) AS rank     FROM portfolio_chunks pc     WHERE pc.tsv @@ plainto_tsquery('english', query_text)     ORDER BY ts_rank_cd(pc.tsv, plainto_tsquery('english', query_text)) DESC     LIMIT match_count * 2 ) SELECT      pc.id,     pc.entity_type,     pc.title,     pc.content,     pc.metadata,     dm.rank AS dense_rank,     sm.rank AS sparse_rank,     (COALESCE(1.0 / (rrf_k + dm.rank), 0.0) + COALESCE(1.0 / (rrf_k + sm.rank), 0.0))::FLOAT AS rrf_score FROM portfolio_chunks pc LEFT JOIN dense_matches dm ON pc.id = dm.id LEFT JOIN sparse_matches sm ON pc.id = sm.id WHERE dm.id IS NOT NULL OR sm.id IS NOT NULL ORDER BY rrf_score DESC LIMIT match_count; $$;