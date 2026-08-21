import asyncio
import json
import uuid
import math
import os
import sys
from datetime import date
from dotenv import load_dotenv
import asyncpg
from google import genai

# Load .env.local first if available, else .env
load_dotenv(".env.local")
load_dotenv(".env")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/portfolio_db")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Strip async driver prefix if present for raw asyncpg connection
if "postgresql+asyncpg://" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

def is_production_db(url: str) -> bool:
    cloud_indicators = ["neon.tech", "amazonaws.com", "supabase.co", "render.com", "elephantsql.com"]
    return any(indicator in url for indicator in cloud_indicators) or ENVIRONMENT.lower() == "production"


def get_embedding(text: str) -> list[float]:
    """Generates 768-dim embedding via Gemini or deterministic fallback vector."""
    if GEMINI_API_KEY:
        try:
            client = genai.Client(api_key=GEMINI_API_KEY)
            from google.genai import types
            response = client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=text,
                config=types.EmbedContentConfig(output_dimensionality=768)
            )
            if response.embeddings and len(response.embeddings) > 0:
                emb = response.embeddings[0].values
                if len(emb) == 768:
                    return list(emb)
        except Exception as e:
            print(f"Gemini API embed fallback triggered: {e}")
    
    # Deterministic pseudo-random normalized 768-dim embedding based on text hash
    h = hash(text)
    raw = [math.sin(h + i) for i in range(768)]
    norm = math.sqrt(sum(x * x for x in raw))
    return [x / norm for x in raw]

SEED_SKILLS = [
    ("Python", "Programming Language", "Expert"),
    ("PyTorch", "ML Framework", "Expert"),
    ("Hugging Face", "ML & NLP", "Expert"),
    ("Natural Language Processing (NLP)", "AI Domain", "Expert"),
    ("Generative AI & LLMs", "AI Domain", "Expert"),
    ("Embeddings & Vector Search (RAG)", "AI Infrastructure", "Expert"),
    ("BERT & Model Guardrails", "AI Safety", "Advanced"),
    ("PySpark & Big Data", "Data Engineering", "Advanced"),
    ("Predictive Modeling (XGBoost/LightGBM)", "Data Science", "Advanced"),
    ("Contrastive Learning & Soft-Prompt Tuning", "NLP Research", "Advanced"),
    ("FastAPI", "Backend Engineering", "Advanced"),
    ("PostgreSQL & pgvector", "Database Systems", "Advanced"),
    ("Apache Kafka", "Event Streaming", "Advanced"),
    ("Docker & AWS", "Cloud & DevOps", "Advanced"),
    ("C/C++", "Programming Language", "Intermediate"),
]

SEED_PROJECTS = [
    {
        "slug": "autonomous-portfolio-agent",
        "title": "Autonomous Portfolio Agent Platform",
        "tagline": "Real-time SSE-streamed conversational AI proxy with polyglot hybrid retrieval & telemetry",
        "problem_statement": "Job market is kinda rough and static portfolio websites fail to engage hiring managers or demonstrate practical AI/ML deployment, real-time guardrails, and hybrid vector retrieval under real production constraints.",
        "solution_overview": "Architected an interactive, SSE-streamed AI agent proxy powered by Gemini, PostgreSQL pgvector hybrid search (HNSW cosine + TSVector FTS + RRF), Redis sliding-window limiters, and Apache Kafka telemetry streaming.",
        "architecture_metadata": {
            "retrieval": "Hybrid Cosine HNSW + TSVector Reciprocal Rank Fusion (k=60)",
            "streaming": "Server-Sent Events (SSE) with agentic UI navigation events",
            "rate_limiting": "Redis sliding-window ZSET Lua script (10 req / 10 min)"
        },
        "impact_metrics": [
            "TTFT (Time to First Token) < 1.2s via SSE streaming",
            "Vector search query latency < 18ms using HNSW cosine index (m=16, ef=64)",
            "100% factual grounding via hybrid vector RAG context injection"
        ],
        "github_url": "coming soon",
        "live_demo_url": "coming soon",
        "is_featured": True,
        "display_order": 1
    },
    {
        "slug": "inter-iit-dream11-predictive-analytics",
        "title": "Inter-IIT Dream11 Predictive Analytics & GenAI",
        "tagline": "Scalable ETL, multi-format player performance modeling & Qwen GenAI explainability pipeline",
        "problem_statement": "Evaluating player performance dynamics across multi-format cricket matches requires processing complex ball-by-ball datasets, non-linear feature engineering, and interpretable predictions.",
        "solution_overview": "Engineered PySpark & Pandas ETL pipelines over 10-year historical ball-by-ball context across 2,500 players. Benchmarked tree-based ensembles (LightGBM, XGBoost, Random Forest, SVR) achieving 27 MAPE, and integrated Qwen-based GenAI for SHAP explainability insights.",
        "architecture_metadata": {
            "etl_framework": "Curated 3 specialized analytics datasets from ball-by-ball cricksheet data: Alone-Player Dataset, Player-Venue Dataset, Player-vs-Player Dataset",
            "predictive_models": "LightGBM, XGBoost, Random Forest, SVR",
            "explainability": "SHAP feature attribution + Qwen GenAI insights"
        },
        "impact_metrics": [
            "Ranked 6th out of 23 IITs (top 26%) at Inter-IIT Tech Meet 13.0 (IIT Bombay)",
            "Processed 10-year historical context for 2,500+ players across T20, ODI, and Test formats",
            "Achieved 27 MAPE with tree-based ensemble models & SHAP explainability"
        ],
        "github_url": None,
        "live_demo_url": "https://drive.google.com/file/d/1gWriRnAOdM3CRNunWbIvk7H2_1gkQE_y/view?usp=sharing",
        "is_featured": True,
        "display_order": 2
    },
    {
        "slug": "attentive-aggregation-embeddings",
        "title": "Attentive Aggregation for Text Embeddings",
        "tagline": "Training-free text embedding enhancement via attention-weighted token pooling",
        "problem_statement": "Mean pooling over transformer token representations loses critical context and over-weights uninformative stop words in dense vector retrieval.",
        "solution_overview": "Developed a novel training-free aggregation method leveraging transformer key-value self-attention weights to compute optimal token representations for Llama-3-1B, boosting top-K recall on retrieval benchmarks.",
        "architecture_metadata": {
            "model_family": "Llama-3-1B-Instruct",
            "aggregation": "Attentive pooling",
            "compute": "PyTorch + HuggingFace Transformers"
        },
        "impact_metrics": [
            "+5% MTEB STS performance improvement and +2% retrieval performance improvement over standard mean pooling",
            "Zero retraining required (100% training-free soft aggregation)"
        ],
        "github_url": None,
        "live_demo_url": "https://canva.link/dl61f3gmnzz18jv",
        "is_featured": True,
        "display_order": 3
    }
]

SEED_EXPERIENCES = [
    {
        "company": "Thuriyam AI",
        "role": "AI & Backend Engineer Intern",
        "location": "Bangalore (Remote)",
        "employment_type": "Internship",
        "start_date": date(2025, 12, 1),
        "end_date": date(2026, 3, 31),
        "summary": "Engineered automated transcription and NLP analysis pipelines using FastAPI and Gemini models on AWS to process 10K+ daily call recordings across sales and support teams at WorkIndia.",
        "achievements": [
            "Engineered automated transcription and NLP analysis pipelines using FastAPI and Gemini models deployed on AWS to process 10K+ daily call recordings.",
            "Architected end-to-end NLP analysis pipelines extracting actionable business intelligence including competitor mentions, top feature requests, and product challenges.",
            "Reduced LLM API costs by 97% on competitor analysis workflows by implementing a deterministic subword pre-filtering engine, routing only 3% of transcripts to heavy AI.",
            "Sustained >99.98% reliability across 300,000+ monthly requests, deploying Dockerized microservices with Jenkins CI/CD automation."
        ]
    },
    {
        "company": "AI Stealth Startup",
        "role": "Data Scientist Intern",
        "location": "Bangalore (Remote)",
        "employment_type": "Internship",
        "start_date": date(2025, 8, 1),
        "end_date": date(2025, 11, 1),
        "summary": "Curated a 150K-sample multi-label AI safety dataset and trained a BERT-based guardrail model achieving 95.8% accuracy with <50 ms latency (>95% faster than LLM guardrails).",
        "achievements": [
            "Curated a 150K-sample multi-label safety dataset (toxic, NSFW, partial-toxic, code, self-harm, illegal, prompt-injection, safe) with 30K test split using data-mining techniques.",
            "Trained a BERT-based guardrail model achieving 95.8% accuracy, 0.96 micro-F1, and <50 ms inference latency (>95% faster than LLM guardrails).",
            "Evaluated per-class safety performance, maintaining >0.83 F1 on NSFW, 0.63 on prompt-injection, and 0.99+ on self-harm and illegal content filtering."
        ]
    },
    {
        "company": "NLP Lab, Indian Institute of Science (IISc)",
        "role": "NLP Research Intern",
        "location": "Bangalore (Hybrid)",
        "employment_type": "Research",
        "start_date": date(2025, 5, 1),
        "end_date": date(2025, 8, 1),
        "summary": "Researched computational cost reduction for LLM encoders in semantic retrieval. Created a 180K+ sample cross-lingual embedding dataset using NV-Retriever hard negative mining.",
        "achievements": [
            "Investigated methods to enhance LLM-based encoders for semantic similarity and retrieval with reduced computational footprint.",
            "Created a 180K+ sample cross-lingual embedding dataset using NV-Retriever hard negative mining (10 hard negatives per anchor with e5-Mistral-7B-Instruct).",
            "Achieved a 5% improvement on Semantic Textual Similarity (STS) benchmarks and 2% improvement on Retrieval benchmarks while training only 0.001% of parameters via soft-prompt tuning."
        ]
    }
]

SEED_TRADEOFFS = [
    {
        "topic": "AI Safety: Lightweight BERT Guardrail vs. Heavy LLM Guardrail",
        "context_slug": "ai-stealth-startup",
        "decision": "Trained a fine-tuned BERT-based guardrail model for 8-class safety classification instead of routing prompt requests through LLM guardrails.",
        "alternatives_considered": ["LLM Guardrail (Llama-Guard / GPT-4-mini)", "Regex / Keyword Blacklists"],
        "rationale": "BERT achieved <50 ms inference latency (>95% faster than LLM guardrails) with 95.8% accuracy and 0.96 micro-F1 while consuming a fraction of GPU compute.",
        "tradeoffs_accepted": "Slightly lower macro-F1 on rare prompt-injection edge cases (0.63) compensated by targeted dataset curation."
    },
    {
        "topic": "LLM API Cost Reduction: Subword Pre-filtering vs. Direct Processing",
        "context_slug": "thuriyam-ai",
        "decision": "Implemented a deterministic subword pre-filtering engine to route transcripts prior to heavy LLM analysis.",
        "alternatives_considered": ["Direct Gemini API Processing for 100% transcripts", "Vector Cosine Similarity Pre-filtering"],
        "rationale": "Pre-filtering routed only the relevant 3% of transcripts to heavy AI analysis without quality loss, reducing LLM API costs by 97% across 300K+ monthly requests.",
        "tradeoffs_accepted": "Requires periodic dictionary updates for emerging competitor keywords and product features."
    },
    {
        "topic": "LLM Fine-Tuning: Soft-Prompt Tuning vs. Full Parameter Tuning",
        "context_slug": "iisc-nlp-lab",
        "decision": "Utilized soft-prompt tuning on e5-Mistral-7B-Instruct with NV-Retriever hard negative mining.",
        "alternatives_considered": ["Full Parameter Fine-Tuning", "LoRA / QLoRA Adapter Tuning"],
        "rationale": "Soft-prompt tuning updated only 0.001% of model parameters while yielding +5% STS and +2% retrieval benchmark improvements, drastically reducing GPU training memory.",
        "tradeoffs_accepted": "Soft prompts require careful embedding initialization to prevent optimization instability during contrastive learning."
    },
    {
        "topic": "Hybrid Search: Reciprocal Rank Fusion (RRF) vs. Linear Score Combination",
        "context_slug": "autonomous-portfolio-agent",
        "decision": "Selected Reciprocal Rank Fusion (RRF with k=60) inside a PostgreSQL SQL function over normalized weighted linear sum.",
        "alternatives_considered": ["Weighted Linear Sum (0.7 * Dense + 0.3 * Sparse)", "Two-stage Cross-Encoder Reranking"],
        "rationale": "RRF requires zero score normalization calibration across different vector scale distributions and runs efficiently in a single database roundtrip.",
        "tradeoffs_accepted": "RRF yields relative rank positions rather than calibrated confidence similarity scores."
    }
]

SEED_CHUNKS = [
    {
        "entity_type": "bio",
        "slug": "about-yogesh",
        "title": "About Yogesh Sharma",
        "content": "Yogesh Sharma is a 2026 undergraduate at IIT Jodhpur pursuing a B.Tech with a Minor in Artificial Intelligence & Data Engineering. He targets AI Engineer, Data Scientist, and ML Engineer roles. Yogesh has completed industry and research internships at Thuriyam AI (FastAPI & Gemini LLM cost optimization), AI Stealth Startup (BERT guardrail safety models & dataset mining), and IISc Bangalore NLP Lab (cross-lingual contrastive embeddings & soft-prompt tuning). He secured 6th rank out of 23 IITs at Inter-IIT Tech Meet 13.0.",
        "metadata": {"category": "general", "author": "Yogesh Sharma", "target_roles": ["AI Engineer", "Data Scientist", "ML Engineer"]}
    },
    {
        "entity_type": "project",
        "slug": "autonomous-portfolio-agent",
        "title": "Autonomous Portfolio Agent Platform",
        "content": "The Autonomous Portfolio Agent is built using FastAPI, PostgreSQL pgvector hybrid search (HNSW cosine + FTS RRF k=60), MongoDB document storage, Redis sliding window limiters, and Apache Kafka telemetry streaming. It streams agent responses via SSE (Server-Sent Events) and issues real-time UI navigation commands.",
        "metadata": {"project_slug": "autonomous-portfolio-agent"}
    },
    {
        "entity_type": "project",
        "slug": "inter-iit-dream11-predictive-analytics",
        "title": "Inter-IIT Dream11 Predictive Analytics & GenAI",
        "content": "Built scalable PySpark and Pandas feature pipelines across 10 years of historical match data for 2,500 players. Benchmarked tree-based ensemble models (LightGBM, XGBoost, Random Forest, SVR) achieving 27 MAPE and securing 6th position out of 23 IITs at Inter-IIT Tech Meet 13.0 (IIT Bombay). Integrated Qwen GenAI for SHAP explainability insights.",
        "metadata": {"project_slug": "inter-iit-dream11-predictive-analytics"}
    },
    {
        "entity_type": "project",
        "slug": "attentive-aggregation-embeddings",
        "title": "Attentive Aggregation for Text Embeddings",
        "content": "Attentive Aggregation is a training-free technique for Llama-3-1B embeddings that uses transformer key-value self-attention weights to aggregate token representations, outperforming standard mean pooling by +4.8% on retrieval benchmarks.",
        "metadata": {"project_slug": "attentive-aggregation-embeddings"}
    },
    {
        "entity_type": "experience",
        "slug": "thuriyam-ai",
        "title": "AI & Backend Engineer Intern at Thuriyam AI",
        "content": "Engineered automated transcription and NLP analysis pipelines using FastAPI and Gemini models on AWS processing 10K+ daily call recordings. Built a deterministic subword pre-filtering engine reducing LLM API costs by 97% while maintaining >99.98% reliability across 300,000+ monthly requests with Dockerized microservices.",
        "metadata": {"company": "Thuriyam AI", "role": "AI & Backend Engineer Intern"}
    },
    {
        "entity_type": "experience",
        "slug": "ai-stealth-startup",
        "title": "Data Scientist Intern at AI Stealth Startup",
        "content": "Curated a 150K-sample multi-label safety dataset and trained a BERT-based guardrail model achieving 95.8% accuracy, 0.96 micro-F1, and <50 ms inference latency (>95% faster than LLM guardrails). Maintained >0.83 F1 on NSFW, 0.63 on prompt injection, and 0.99+ on self-harm/illegal content.",
        "metadata": {"company": "AI Stealth Startup", "role": "Data Scientist Intern"}
    },
    {
        "entity_type": "experience",
        "slug": "iisc-nlp-lab",
        "title": "NLP Research Intern at IISc Bangalore NLP Lab",
        "content": "Researched computational cost reduction for LLM encoders in semantic retrieval. Created a 180K+ sample cross-lingual embedding dataset using NV-Retriever hard negative mining with e5-Mistral-7B-Instruct. Achieved 5% STS improvement and 2% retrieval improvement via soft-prompt tuning on 0.001% parameters.",
        "metadata": {"company": "IISc Bangalore NLP Lab", "role": "NLP Research Intern"}
    },
    {
        "entity_type": "tradeoff",
        "slug": "bert-guardrail-tradeoff",
        "title": "Architectural Rationale: BERT Guardrail vs LLM Moderation",
        "content": "Why fine-tuned BERT over LLM guardrails? Sub-50ms latency is mandatory for real-time AI safety filtering. BERT achieved 95.8% accuracy at >95% speed improvement over heavy LLM guardrails while reducing compute cost exponentially.",
        "metadata": {"topic": "AI Safety"}
    },
    {
        "entity_type": "tradeoff",
        "slug": "llm-prefiltering-tradeoff",
        "title": "Architectural Rationale: Subword Pre-filtering Engine",
        "content": "Why subword pre-filtering? Processing 100% of raw audio transcripts with heavy LLM models incurs massive API overhead. Routing only the 3% of filtered relevant transcripts reduced LLM costs by 97% with zero loss in competitor intelligence extraction quality.",
        "metadata": {"topic": "Cost Optimization"}
    },
    {
        "entity_type": "education",
        "slug": "iit-jodhpur",
        "title": "Education & Academic Background at IIT Jodhpur",
        "content": "Indian Institute of Technology (IIT) Jodhpur (2022 - 2026). Degree: B.Tech in Chemical Engineering with Minor in Artificial Intelligence & Data Engineering (CGPA: 7.79). Core coursework: Machine Learning, Deep Learning, Probability & Statistics, Linear Algebra, Data Structures & Algorithms. Achievements: 6th out of 23 IITs at Inter-IIT Tech Meet 13.0, Top 10 ML Kaggle Challenge worldwide by RAID.",
        "metadata": {"institution": "IIT Jodhpur", "degree": "B.Tech + Minor in AI & Data Engineering"}
    }
]

async def seed():
    print(f"Connecting to database at {DATABASE_URL}...")
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        print("Ensuring tables and HNSW / TSVector extensions exist...")
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        schema_path = os.path.join(base_dir, "docs", "database", "postgres_schema.sql")
        with open(schema_path, "r") as f:
            schema_sql = f.read()
        await conn.execute(schema_sql)
        print("PostgreSQL schema initialized successfully.")

        # Clean existing tables for fresh seed
        print("Cleaning existing portfolio records...")
        await conn.execute("DELETE FROM portfolio_chunks;")
        await conn.execute("DELETE FROM system_tradeoffs;")
        await conn.execute("DELETE FROM experiences;")
        await conn.execute("DELETE FROM projects;")
        await conn.execute("DELETE FROM skills;")

        # Seed Skills
        print("Seeding Skills...")
        for name, category, prof in SEED_SKILLS:
            await conn.execute(
                """
                INSERT INTO skills (name, category, proficiency_level)
                VALUES ($1, $2, $3)
                ON CONFLICT (name) DO UPDATE SET category = EXCLUDED.category, proficiency_level = EXCLUDED.proficiency_level
                """,
                name, category, prof
            )

        # Seed Projects
        print("Seeding Projects...")
        for p in SEED_PROJECTS:
            await conn.execute(
                """
                INSERT INTO projects (slug, title, tagline, problem_statement, solution_overview, architecture_metadata, impact_metrics, github_url, live_demo_url, is_featured, display_order)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (slug) DO UPDATE SET
                    title = EXCLUDED.title,
                    tagline = EXCLUDED.tagline,
                    problem_statement = EXCLUDED.problem_statement,
                    solution_overview = EXCLUDED.solution_overview,
                    architecture_metadata = EXCLUDED.architecture_metadata,
                    impact_metrics = EXCLUDED.impact_metrics;
                """,
                p["slug"], p["title"], p["tagline"], p["problem_statement"], p["solution_overview"],
                json.dumps(p["architecture_metadata"]), json.dumps(p["impact_metrics"]),
                p["github_url"], p["live_demo_url"], p["is_featured"], p["display_order"]
            )

        # Seed Experiences
        print("Seeding Experience...")
        for exp in SEED_EXPERIENCES:
            await conn.execute(
                """
                INSERT INTO experiences (company, role, location, employment_type, start_date, end_date, summary, achievements)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                exp["company"], exp["role"], exp["location"], exp["employment_type"],
                exp["start_date"], exp["end_date"], exp["summary"], exp["achievements"]
            )

        # Seed Tradeoffs
        print("Seeding System Tradeoffs...")
        for t in SEED_TRADEOFFS:
            await conn.execute(
                """
                INSERT INTO system_tradeoffs (topic, context_slug, decision, alternatives_considered, rationale, tradeoffs_accepted)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                t["topic"], t["context_slug"], t["decision"], t["alternatives_considered"], t["rationale"], t["tradeoffs_accepted"]
            )

        # Seed Chunks (Embeddings + TSVector)
        print("Seeding Knowledge Chunks into portfolio_chunks with 768-dim vectors...")
        for chunk in SEED_CHUNKS:
            text_for_embed = f"{chunk['title']} {chunk['content']}"
            embedding = get_embedding(text_for_embed)
            vec_str = f"[{','.join(str(x) for x in embedding)}]"
            
            await conn.execute(
                """
                INSERT INTO portfolio_chunks (entity_type, slug, title, content, metadata, embedding)
                VALUES ($1, $2, $3, $4, $5, $6::vector)
                """,
                chunk["entity_type"], chunk["slug"], chunk["title"], chunk["content"],
                json.dumps(chunk["metadata"]), vec_str
            )

        print("Database Seeding Completed Successfully! All AI/ML portfolio chunks and SQL records ready.")

    finally:
        await conn.close()

if __name__ == "__main__":
    confirm_prod = "--confirm-prod" in sys.argv or "--prod" in sys.argv
    if is_production_db(DATABASE_URL) and not confirm_prod:
        masked_url = DATABASE_URL
        if "@" in masked_url:
            user_part, host_part = masked_url.split("@", 1)
            masked_url = f"{user_part.split('://')[0]}://***:***@{host_part}"
        print(f"\n[ERROR] Production/Cloud database target detected!")
        print(f"Target URL: {masked_url}")
        print(f"To seed a production database, pass '--confirm-prod': python scripts/seed_data.py --confirm-prod\n")
        sys.exit(1)
    
    asyncio.run(seed())

