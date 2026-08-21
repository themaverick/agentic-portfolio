import asyncio
import json
import time
import uuid
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from google import genai
from google.genai import types

from app.core.config import settings
from app.core.kafka import produce_event
from app.services.retrieval import (
    search_all_entities_hybrid,
    search_projects_hybrid,
    search_experiences_hybrid,
    search_faqs_hybrid
)

SYSTEM_PROMPT = """You are the official AI Technical Proxy for Yogesh Sharma, a 2026 B.Tech undergraduate from IIT Jodhpur with a Minor in Artificial Intelligence & Data Engineering. Yogesh is targeting AI Engineer, Data Scientist, and Machine Learning Engineer roles. Your purpose is to represent Yogesh's skills, experience across Thuriyam AI, AI Stealth Startup, and IISc Bangalore NLP Lab, and system design philosophies to technical recruiters, hiring managers, and engineers.

Core Behavioral Directives:
1. Factual Grounding: You MUST strictly answer questions using information retrieved from the PostgreSQL vector database (projects, experiences, and technical FAQs). NEVER invent, exaggerate, or assume work experience, degrees, or project metrics.
2. Relational Context: When discussing a project, work experience, or technical trade-off, explicitly highlight which company or project it is associated with.
3. Tone & Style: Confident, candid, concise, and technically grounded. Speak as Yogesh's authorized proxy.
4. Refusal Policy: Politely refuse non-portfolio tasks (e.g. general math, creative writing, generic programming).
"""

def format_sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"

async def stream_agent_chat(
    session_id: str,
    user_message: str,
    db: AsyncSession
) -> AsyncGenerator[str, None]:
    """
    Streams SSE events for agent chat:
    - event: handshake
    - event: tool_start
    - event: ui_action
    - event: chunk
    - event: done
    """
    start_time = time.time()
    yield format_sse("handshake", {"session_id": session_id, "status": "connected"})

    query_lower = user_message.lower()
    tool_calls_executed = []
    retrieved_context = ""
    target_project_slug = None
    target_company_slug = None

    # Determine tool execution based on intent
    if "project" in query_lower:
        yield format_sse("tool_start", {"tool": "search_projects", "query": user_message})
        tool_calls_executed.append("search_projects")
        try:
            projects = await search_projects_hybrid(db, user_message, match_count=3)
            if projects:
                retrieved_context = "\n---\n".join([
                    f"[Project: {p['title']}]\nTagline: {p['tagline']}\nProblem: {p['problem_statement']}\nSolution: {p['solution_overview']}"
                    for p in projects
                ])
                target_project_slug = projects[0]["slug"]
        except Exception as e:
            print(f"search_projects error: {e}")

    elif any(k in query_lower for k in ["experience", "work", "job", "intern", "company", "thuriyam", "iisc"]):
        yield format_sse("tool_start", {"tool": "search_experiences", "query": user_message})
        tool_calls_executed.append("search_experiences")
        try:
            experiences = await search_experiences_hybrid(db, user_message, match_count=3)
            if experiences:
                retrieved_context = "\n---\n".join([
                    f"[Experience: {e['role']} at {e['company']}]\nSummary: {e['summary']}\nAchievements: {' '.join(e.get('achievements', []))}"
                    for e in experiences
                ])
                target_company_slug = experiences[0]["company"].lower().replace(" ", "-")
        except Exception as e:
            print(f"search_experiences error: {e}")

    else:
        # Default: Unified Multi-Entity Retriever (Projects + Experiences + FAQs)
        yield format_sse("tool_start", {"tool": "search_all_entities_hybrid", "query": user_message})
        tool_calls_executed.append("search_all_entities_hybrid")
        try:
            entities = await search_all_entities_hybrid(db, user_message, top_k=5)
            if entities:
                context_blocks = []
                for ent in entities:
                    context_blocks.append(f"[{ent['title']}]\n{ent['content']}")
                    if ent.get("related_project_slug") and not target_project_slug:
                        target_project_slug = ent["related_project_slug"]
                    if ent.get("related_company_slug") and not target_company_slug:
                        target_company_slug = ent["related_company_slug"]
                retrieved_context = "\n---\n".join(context_blocks)
        except Exception as e:
            print(f"search_all_entities_hybrid error: {e}")

    # Emit UI Navigation based on entity relationships
    if target_project_slug or "project" in query_lower:
        yield format_sse("ui_action", {"action": "navigate", "route": "/projects", "target": target_project_slug or "projects-grid"})
        tool_calls_executed.append("navigate_ui")
    elif target_company_slug or any(k in query_lower for k in ["experience", "work", "job", "intern"]):
        yield format_sse("ui_action", {"action": "navigate", "route": "/experience", "target": target_company_slug or "experience-timeline"})
        tool_calls_executed.append("navigate_ui")

    # Formulate Gemini prompt with grounded context
    prompt_text = f"{SYSTEM_PROMPT}\n\nUser Question: {user_message}\n"
    if retrieved_context:
        prompt_text += f"\nRetrieved Relational Context (Projects, Experiences, FAQs):\n{retrieved_context}\n"

    generated_text = ""
    prompt_tokens = len(prompt_text) // 4
    completion_tokens = 0

    if settings.GEMINI_API_KEY:
        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            response = client.models.generate_content_stream(
                model=settings.GEMINI_MODEL,
                contents=prompt_text,
            )
            for chunk in response:
                if chunk.text:
                    generated_text += chunk.text
                    yield format_sse("chunk", {"token": chunk.text})
                    await asyncio.sleep(0.01)
        except Exception as e:
            print(f"Gemini streaming error, using fallback: {e}")
            generated_text = ""

    if not generated_text:
        # Grounded fallback response
        if retrieved_context:
            fallback_response = f"Based on Yogesh's portfolio database records:\n\n{retrieved_context}\n\nYogesh Sharma is a 2026 IIT Jodhpur undergraduate specializing in Applied AI, High-Performance Systems, Vector DB Retrieval, and Distributed Architectures."
        else:
            fallback_response = "I am Yogesh's AI Technical Proxy! Ask me about Yogesh Sharma's engineering projects (like the Autonomous Portfolio Agent platform and Attentive Aggregation), work experience at Thuriyam AI, AI Stealth Startup, and IISc NLP Lab, or core system design trade-offs."
        
        words = fallback_response.split(" ")
        for i in range(0, len(words), 3):
            chunk_str = " ".join(words[i:i+3]) + " "
            generated_text += chunk_str
            yield format_sse("chunk", {"token": chunk_str})

    completion_tokens = len(generated_text) // 4
    total_ms = (time.time() - start_time) * 1000

    yield format_sse("done", {
        "session_id": session_id,
        "total_ms": round(total_ms, 2),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens
    })

    # Produce telemetry event to Kafka
    telemetry_payload = {
        "event_id": str(uuid.uuid4()),
        "session_id": session_id,
        "endpoint": "/api/v1/agent/chat",
        "model_version": settings.GEMINI_MODEL,
        "latency_breakdown": {"total_ms": round(total_ms, 2)},
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "tool_calls_executed": tool_calls_executed,
        "status_code": 200
    }
    await produce_event("agent-telemetry", telemetry_payload, key=session_id)
