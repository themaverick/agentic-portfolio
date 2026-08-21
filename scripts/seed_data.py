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

SEED_FAQS = [
    {
        "question": "What is Yogesh's background, education, and target career roles?",
        "answer": "Yogesh Sharma is a 2026 B.Tech undergraduate at IIT Jodhpur with a Minor in Artificial Intelligence & Data Engineering. He targets AI Engineer, Data Scientist, and Machine Learning Engineer roles. He specializes in LLMs, RAG retrieval architectures, vector databases, high-performance backends, and AI safety guardrails.",
        "category": "general",
        "related_project_slug": None,
        "related_company_slug": None,
    },
    {
        "question": "Why did you build a BERT guardrail model instead of using LLM guardrails at AI Stealth Startup?",
        "answer": "Sub-50ms latency was mandatory for real-time safety filtering. Fine-tuned BERT achieved 95.8% accuracy and 0.96 micro-F1 at >95% speed improvement over heavy LLM guardrails (like Llama-Guard or GPT-4-mini) while consuming a fraction of GPU compute costs.",
        "category": "technical_tradeoff",
        "related_project_slug": None,
        "related_company_slug": "ai-stealth-startup",
    },
    {
        "question": "How did you achieve 97% LLM cost reduction at Thuriyam AI?",
        "answer": "Engineered a deterministic subword pre-filtering engine to route transcripts prior to heavy Gemini LLM analysis. This routed only the 3% of relevant transcripts containing competitor mentions or feature requests, reducing API overhead by 97% while maintaining >99.98% reliability across 300K+ monthly requests.",
        "category": "technical_tradeoff",
        "related_project_slug": None,
        "related_company_slug": "thuriyam-ai",
    },
    {
        "question": "How does soft-prompt tuning work in your IISc Bangalore NLP Lab research?",
        "answer": "Utilized soft-prompt tuning on e5-Mistral-7B-Instruct with NV-Retriever hard negative mining. By updating only 0.001% of model parameters, we achieved a +5% STS improvement and +2% retrieval improvement while drastically reducing GPU training memory requirements.",
        "category": "technical_tradeoff",
        "related_project_slug": None,
        "related_company_slug": "iisc-nlp-lab",
    },
    {
        "question": "How is the Autonomous Portfolio Agent platform architected?",
        "answer": "The platform is built with FastAPI, PostgreSQL pgvector hybrid search (HNSW cosine + TSVector FTS), MongoDB document storage, Redis sliding-window limiters, and Apache Kafka telemetry streaming. It streams agent responses via SSE (Server-Sent Events) and issues real-time UI navigation commands.",
        "category": "architecture",
        "related_project_slug": "autonomous-portfolio-agent",
        "related_company_slug": None,
    },
    {
        "question": "What techniques were used in the Inter-IIT Dream11 Predictive Analytics project?",
        "answer": "Processed 10 years of historical match data for 2,500 players using PySpark/Pandas pipelines. Benchmarked tree-based ensemble models (LightGBM, XGBoost, Random Forest, SVR) achieving 27 MAPE, and integrated Qwen GenAI for SHAP explainability, securing 6th position out of 23 IITs at Inter-IIT Tech Meet 13.0.",
        "category": "architecture",
        "related_project_slug": "inter-iit-dream11-predictive-analytics",
        "related_company_slug": None,
    },
    {
        "question": "What is Attentive Aggregation for text embeddings?",
        "answer": "Attentive Aggregation is a training-free token pooling technique for transformer models (such as Llama-3-1B). It uses key-value self-attention weights to aggregate token representations, outperforming standard mean pooling by +4.8% on retrieval benchmarks without requiring model retraining.",
        "category": "architecture",
        "related_project_slug": "attentive-aggregation-embeddings",
        "related_company_slug": None,
    },
    {
        "question": "Why use Reciprocal Rank Fusion (RRF) for hybrid search?",
        "answer": "RRF (with k=60) combines dense vector rankings (HNSW cosine) with sparse text rankings (TSVector FTS) without requiring arbitrary score normalization across different score distributions. It runs efficiently inside a single PostgreSQL query.",
        "category": "technical_tradeoff",
        "related_project_slug": "autonomous-portfolio-agent",
        "related_company_slug": None,
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
        await conn.execute("DELETE FROM system_tradeoffs;")
        await conn.execute("DELETE FROM faqs;")
        await conn.execute("DELETE FROM experiences;")
        await conn.execute("DELETE FROM projects;")
        await conn.execute("DELETE FROM skills;")

        # 1. Seed Skills
        print("Seeding Skills...")
        for name, category, proficiency in SEED_SKILLS:
            await conn.execute(
                """
                INSERT INTO skills (name, category, proficiency_level)
                VALUES ($1, $2, $3)
                ON CONFLICT (name) DO UPDATE SET category = EXCLUDED.category, proficiency_level = EXCLUDED.proficiency_level
                """,
                name, category, proficiency
            )

        # 2. Seed Projects with Direct Vector Embeddings
        print("Seeding Projects with Direct Vector Embeddings...")
        for proj in SEED_PROJECTS:
            text_to_embed = f"{proj['title']} - {proj['tagline']}. Problem: {proj['problem_statement']}. Solution: {proj['solution_overview']}"
            embedding = get_embedding(text_to_embed)
            vec_str = f"[{','.join(str(x) for x in embedding)}]"

            await conn.execute(
                """
                INSERT INTO projects (slug, title, tagline, problem_statement, solution_overview, architecture_metadata, impact_metrics, github_url, live_demo_url, is_featured, display_order, embedding)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, CAST($12 AS vector))
                """,
                proj["slug"], proj["title"], proj["tagline"], proj["problem_statement"],
                proj["solution_overview"], json.dumps(proj["architecture_metadata"]),
                json.dumps(proj["impact_metrics"]), proj["github_url"], proj["live_demo_url"],
                proj["is_featured"], proj["display_order"], vec_str
            )

        # 3. Seed Experiences with Direct Vector Embeddings
        print("Seeding Experiences with Direct Vector Embeddings...")
        for exp in SEED_EXPERIENCES:
            text_to_embed = f"{exp['role']} at {exp['company']}. Summary: {exp['summary']} Achievements: {' '.join(exp['achievements'])}"
            embedding = get_embedding(text_to_embed)
            vec_str = f"[{','.join(str(x) for x in embedding)}]"

            await conn.execute(
                """
                INSERT INTO experiences (company, role, location, employment_type, start_date, end_date, summary, achievements, embedding)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, CAST($9 AS vector))
                """,
                exp["company"], exp["role"], exp["location"], exp["employment_type"],
                exp["start_date"], exp["end_date"], exp["summary"], exp["achievements"], vec_str
            )

        # 4. Seed Relational FAQs with Direct Vector Embeddings
        print("Seeding Relational FAQs with Direct Vector Embeddings...")
        for faq in SEED_FAQS:
            text_to_embed = f"Question: {faq['question']} Answer: {faq['answer']}"
            embedding = get_embedding(text_to_embed)
            vec_str = f"[{','.join(str(x) for x in embedding)}]"

            await conn.execute(
                """
                INSERT INTO faqs (question, answer, category, related_project_slug, related_company_slug, embedding)
                VALUES ($1, $2, $3, $4, $5, CAST($6 AS vector))
                """,
                faq["question"], faq["answer"], faq["category"],
                faq["related_project_slug"], faq["related_company_slug"], vec_str
            )

        # 5. Seed System Tradeoffs
        print("Seeding System Tradeoffs...")
        for t in SEED_TRADEOFFS:
            await conn.execute(
                """
                INSERT INTO system_tradeoffs (topic, context_slug, decision, alternatives_considered, rationale, tradeoffs_accepted)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                t["topic"], t["context_slug"], t["decision"], t["alternatives_considered"],
                t["rationale"], t["tradeoffs_accepted"]
            )

        print("Database Seeding Completed Successfully! All primary entities (Projects, Experiences, FAQs) vectorized.")

    finally:
        await conn.close()

if __name__ == "__main__":
    if is_production_db(DATABASE_URL) and "--confirm-prod" not in sys.argv:
        print("\n" + "="*80)
        print("CRITICAL WARNING: DETECTED PRODUCTION CLOUD DATABASE")
        print(f"Connection URL: {DATABASE_URL}")
        print("Execution aborted to protect production data.")
        print("To override and seed production, run: python scripts/seed_data.py --confirm-prod")
        print("="*80 + "\n")
        sys.exit(1)

    asyncio.run(seed())
