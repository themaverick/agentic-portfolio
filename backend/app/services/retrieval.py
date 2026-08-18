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


async def search_portfolio_hybrid(
    db: AsyncSession, query: str, match_count: int = 5, rrf_k: int = 60
) -> List[Dict[str, Any]]:
    """
    Executes PostgreSQL Reciprocal Rank Fusion (RRF) hybrid search
    combining dense vector HNSW cosine distance + sparse TSVector text rank.
    """
    embedding = get_query_embedding(query)
    vec_str = f"[{','.join(str(x) for x in embedding)}]"

    sql_query = text(
        """
        SELECT id, entity_type, title, content, metadata, rrf_score
        FROM match_portfolio_hybrid(:query_text, CAST(:query_embedding AS vector), :match_count, :rrf_k)
        """
    )

    result = await db.execute(
        sql_query,
        {
            "query_text": query,
            "query_embedding": vec_str,
            "match_count": match_count,
            "rrf_k": rrf_k,
        },
    )

    rows = result.mappings().all()
    results = []
    for row in rows:
        results.append(
            {
                "id": str(row["id"]),
                "entity_type": row["entity_type"],
                "title": row["title"],
                "content": row["content"],
                "metadata": row["metadata"],
                "rrf_score": float(row["rrf_score"]),
            }
        )
    return results
