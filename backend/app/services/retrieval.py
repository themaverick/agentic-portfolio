import math
from typing import Any, Dict, List
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from google import genai
from app.core.config import settings


def get_query_embedding(query_text: str) -> List[float]:
    """Generates 768-dim vector embedding for incoming search query."""
    if settings.GEMINI_API_KEY:
        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            from google.genai import types
            response = client.models.embed_content(
                model=settings.EMBEDDING_MODEL,
                contents=query_text,
                config=types.EmbedContentConfig(output_dimensionality=768)
            )
            if response.embeddings and len(response.embeddings) > 0:
                emb = response.embeddings[0].values
                if len(emb) == 768:
                    return list(emb)
        except Exception as e:
            print(f"Gemini query embedding fallback: {e}")

    # Normalized deterministic fallback vector
    h = hash(query_text)
    raw = [math.sin(h + i) for i in range(768)]
    norm = math.sqrt(sum(x * x for x in raw))
    return [x / norm for x in raw]


async def search_projects_hybrid(
    db: AsyncSession, query: str, match_count: int = 3
) -> List[Dict[str, Any]]:
    """Hybrid search over projects (HNSW cosine + TSVector FTS + RRF)."""
    embedding = get_query_embedding(query)
    vec_str = f"[{','.join(str(x) for x in embedding)}]"

    sql_query = text(
        """
        SELECT id, slug, title, tagline, problem_statement, solution_overview, architecture_metadata, impact_metrics, rrf_score
        FROM match_projects_hybrid(:query_text, CAST(:query_embedding AS vector), :match_count)
        """
    )
    result = await db.execute(sql_query, {"query_text": query, "query_embedding": vec_str, "match_count": match_count})
    rows = result.mappings().all()
    return [dict(row) for row in rows]


async def search_experiences_hybrid(
    db: AsyncSession, query: str, match_count: int = 3
) -> List[Dict[str, Any]]:
    """Hybrid search over professional experiences (HNSW cosine + TSVector FTS + RRF)."""
    embedding = get_query_embedding(query)
    vec_str = f"[{','.join(str(x) for x in embedding)}]"

    sql_query = text(
        """
        SELECT id, company, role, summary, achievements, rrf_score
        FROM match_experiences_hybrid(:query_text, CAST(:query_embedding AS vector), :match_count)
        """
    )
    result = await db.execute(sql_query, {"query_text": query, "query_embedding": vec_str, "match_count": match_count})
    rows = result.mappings().all()
    return [dict(row) for row in rows]


async def search_faqs_hybrid(
    db: AsyncSession, query: str, match_count: int = 4
) -> List[Dict[str, Any]]:
    """Hybrid search over FAQs and system design rationale (HNSW cosine + TSVector FTS + RRF)."""
    embedding = get_query_embedding(query)
    vec_str = f"[{','.join(str(x) for x in embedding)}]"

    sql_query = text(
        """
        SELECT id, question, answer, category, related_project_slug, related_company_slug, rrf_score
        FROM match_faqs_hybrid(:query_text, CAST(:query_embedding AS vector), :match_count)
        """
    )
    result = await db.execute(sql_query, {"query_text": query, "query_embedding": vec_str, "match_count": match_count})
    rows = result.mappings().all()
    return [dict(row) for row in rows]


async def search_all_entities_hybrid(
    db: AsyncSession, query: str, top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Combined multi-entity hybrid retriever searching projects, experiences, and relational FAQs.
    """
    projects = await search_projects_hybrid(db, query, match_count=3)
    experiences = await search_experiences_hybrid(db, query, match_count=3)
    faqs = await search_faqs_hybrid(db, query, match_count=4)

    combined = []
    for p in projects:
        combined.append({
            "entity_type": "project",
            "title": f"Project: {p['title']}",
            "content": f"Tagline: {p['tagline']}\nProblem: {p['problem_statement']}\nSolution: {p['solution_overview']}",
            "project_slug": p["slug"],
            "rrf_score": float(p["rrf_score"])
        })

    for e in experiences:
        achievements_str = " ".join(e["achievements"]) if e.get("achievements") else ""
        combined.append({
            "entity_type": "experience",
            "title": f"Experience: {e['role']} at {e['company']}",
            "content": f"Summary: {e['summary']}\nKey Achievements: {achievements_str}",
            "company_slug": e["company"].lower().replace(" ", "-"),
            "rrf_score": float(e["rrf_score"])
        })

    for f in faqs:
        combined.append({
            "entity_type": "faq",
            "title": f"Q: {f['question']}",
            "content": f"A: {f['answer']}",
            "related_project_slug": f.get("related_project_slug"),
            "related_company_slug": f.get("related_company_slug"),
            "rrf_score": float(f["rrf_score"])
        })

    # Sort combined results by RRF score
    combined.sort(key=lambda x: x["rrf_score"], reverse=True)
    return combined[:top_k]
