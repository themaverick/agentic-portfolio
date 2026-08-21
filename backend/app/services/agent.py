import asyncio
import json
import time
import uuid
from typing import AsyncGenerator, Dict, Any, Tuple, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from google import genai
from google.genai import types

from app.core.config import settings
from app.core.kafka import produce_event
from app.core.redis import get_redis
from app.services.retrieval import (
    search_all_entities_hybrid,
    search_projects_hybrid,
    search_experiences_hybrid,
    search_faqs_hybrid
)

# --- Fallback In-Memory Session Storage ---
IN_MEMORY_SESSIONS: Dict[str, List[Dict[str, str]]] = {}

async def load_session_history(session_id: str, max_turns: int = 10) -> List[Dict[str, str]]:
    """Loads session turn history from Redis or in-memory fallback cache."""
    try:
        r = get_redis()
        raw_data = await r.get(f"session:{session_id}:history")
        if raw_data:
            turns = json.loads(raw_data)
            return turns[-max_turns:]
    except Exception as e:
        print(f"Redis session history load error (using in-memory fallback): {e}")
    
    return IN_MEMORY_SESSIONS.get(session_id, [])[-max_turns:]

async def save_session_history(session_id: str, user_msg: str, assistant_response: str):
    """Persists user and assistant response turns to Redis and in-memory fallback cache."""
    turns = await load_session_history(session_id, max_turns=20)
    turns.append({"role": "user", "content": user_msg})
    turns.append({"role": "model", "content": assistant_response})
    
    IN_MEMORY_SESSIONS[session_id] = turns

    try:
        r = get_redis()
        await r.set(f"session:{session_id}:history", json.dumps(turns), ex=86400)
    except Exception as e:
        print(f"Redis session history save error: {e}")

def build_gemini_history(past_turns: List[Dict[str, str]]) -> List[types.Content]:
    """Converts stored turn dictionary objects to Gemini types.Content objects."""
    contents = []
    for turn in past_turns:
        role = turn.get("role", "user")
        text = turn.get("content", "")
        if text:
            contents.append(
                types.Content(
                    role="user" if role == "user" else "model",
                    parts=[types.Part(text=text)]
                )
            )
    return contents

# --- Tool Declarations for Gemini Function Calling ---

def search_projects(query: str) -> str:
    """Search ONLY Yogesh Sharma's software projects, architectures, and technical codebases.
    
    Use this tool exclusively when the user asks about projects, systems built, GitHub repos, or implementation specs.
    Returns: Markdown string containing project title, tagline, problem statement, and solution overview for matching projects.
    DO NOT use for work experience, employment history, or system design trade-off FAQs.
    """
    return ""

def search_experiences(query: str) -> str:
    """Search ONLY Yogesh Sharma's professional employment, internships, work achievements, and role details.
    
    Use this tool exclusively when the user asks about work history, internships, or roles at Thuriyam AI, IISc Bangalore, or AI Stealth Startup.
    Returns: Markdown string containing role, company name, summary, and achievements for matching experiences.
    DO NOT use for software projects or technical FAQs.
    """
    return ""

def search_faqs(query: str) -> str:
    """Search ONLY Yogesh Sharma's technical FAQs, engineering philosophy, and system design trade-offs.
    
    Use this tool exclusively when the user asks about specific architectural choices or technical trade-offs (e.g. RRF vs Linear search, Kafka vs Celery, pgvector vs Pinecone).
    Returns: Markdown string containing technical questions and detailed answers for matching FAQs.
    DO NOT use for general project lists or work history.
    """
    return ""

def search_all_entities(query: str) -> str:
    """Unified search across all portfolio records (projects, experiences, and technical FAQs).
    
    Use this tool ONLY when the user's request is broad, ambiguous, or explicitly asks for an overview of everything Yogesh has done.
    Returns: Markdown string containing top matching entities across all categories.
    DO NOT call alongside specific tools.
    """
    return ""

def navigate_ui(route: str, target: str) -> str:
    """Trigger frontend UI navigation to a route ('/projects' or '/experience') and scroll to a target section or element ID.
    
    Use this tool ONLY when the user explicitly asks to navigate, go to a section, or view a page.
    Returns: Navigation status confirmation.
    """
    return ""

AVAILABLE_TOOLS = [search_projects, search_experiences, search_faqs, search_all_entities, navigate_ui]

SYSTEM_PROMPT = """You are the official AI Technical Proxy for Yogesh Sharma, a 2026 B.Tech undergraduate from IIT Jodhpur with a Minor in Artificial Intelligence & Data Engineering. Yogesh is targeting AI Engineer, Data Scientist, and Machine Learning Engineer roles. Your purpose is to represent Yogesh's skills, experience across Thuriyam AI, AI Stealth Startup, and IISc Bangalore NLP Lab, and system design philosophies to technical recruiters, hiring managers, and engineers.

Core Behavioral Directives:
1. Tool Efficiency Policy: Select ONLY the SINGLE most specific tool that directly answers the user's intent:
   - For questions about projects, applications, or code -> call ONLY search_projects.
   - For questions about jobs, internships, or companies -> call ONLY search_experiences.
   - For questions about system design trade-offs or technical FAQs -> call ONLY search_faqs.
   - For broad queries asking for a full summary of everything -> call ONLY search_all_entities.
   - DO NOT call multiple tools unless the user explicitly requests an exhaustive multi-category audit.
2. Reasoning Directive: Before invoking tools or giving an answer, ALWAYS state your concise step-by-step reasoning inside a block starting with 'THOUGHT:' and ending with 'END_THOUGHT'.
3. Factual Grounding: You MUST strictly answer questions using information retrieved from the database via tools. NEVER invent work experience, degrees, or project metrics.
4. Tone & Style: Confident, candid, concise, and technically grounded. Speak as Yogesh's authorized proxy.
5. Refusal Policy: Politely refuse non-portfolio tasks (e.g. general math, creative writing, generic programming).
"""

def format_sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"

async def _execute_backend_tool(
    tool_name: str,
    tool_args: Dict[str, Any],
    user_message: str,
    db: AsyncSession
) -> Tuple[str, Optional[str], Optional[str], Optional[Dict[str, str]]]:
    """
    Executes real database queries or UI action based on Gemini tool calls.
    Returns: (context_string, target_project_slug, target_company_slug, ui_action_dict)
    """
    query = tool_args.get("query") or user_message
    context = ""
    proj_slug = None
    comp_slug = None
    ui_action = None

    if tool_name == "search_projects":
        results = await search_projects_hybrid(db, query, match_count=3)
        if results:
            context = "\n---\n".join([
                f"[Project: {p['title']}]\nTagline: {p['tagline']}\nProblem: {p['problem_statement']}\nSolution: {p['solution_overview']}"
                for p in results
            ])
            proj_slug = results[0]["slug"]
        else:
            context = "No matching projects found in database."

    elif tool_name == "search_experiences":
        results = await search_experiences_hybrid(db, query, match_count=3)
        if results:
            context = "\n---\n".join([
                f"[Experience: {e['role']} at {e['company']}]\nSummary: {e['summary']}\nAchievements: {' '.join(e.get('achievements', []))}"
                for e in results
            ])
            comp_slug = results[0]["company"].lower().replace(" ", "-")
        else:
            context = "No matching work experience found in database."

    elif tool_name == "search_faqs":
        results = await search_faqs_hybrid(db, query, match_count=3)
        if results:
            context = "\n---\n".join([
                f"[FAQ: {f['question']}]\nAnswer: {f['answer']}"
                for f in results
            ])
        else:
            context = "No matching technical FAQs found in database."

    elif tool_name == "search_all_entities":
        results = await search_all_entities_hybrid(db, query, top_k=5)
        if results:
            context_blocks = []
            for ent in results:
                context_blocks.append(f"[{ent['title']}]\n{ent['content']}")
                if ent.get("related_project_slug") and not proj_slug:
                    proj_slug = ent["related_project_slug"]
                if ent.get("related_company_slug") and not comp_slug:
                    comp_slug = ent["related_company_slug"]
            context = "\n---\n".join(context_blocks)
        else:
            context = "No matching entities found in database."

    elif tool_name == "navigate_ui":
        route = tool_args.get("route", "/projects")
        target = tool_args.get("target", "")
        ui_action = {"action": "navigate", "route": route, "target": target}
        context = f"UI navigation executed to route '{route}', target '{target}'."

    return context, proj_slug, comp_slug, ui_action

async def stream_agent_chat(
    session_id: str,
    user_message: str,
    db: AsyncSession
) -> AsyncGenerator[str, None]:
    """
    Streams SSE events for agent chat:
    - event: handshake
    - event: thought
    - event: tool_call / tool_start
    - event: ui_action
    - event: chunk
    - event: done
    """
    start_time = time.time()
    yield format_sse("handshake", {"session_id": session_id, "status": "connected"})

    # Emit initial thought process event immediately so UI renders Thought Process box
    yield format_sse("thought", {"token": f"Analyzing query intent for prompt: '{user_message}'..."})

    tool_calls_executed = []
    generated_text = ""
    prompt_tokens = len(user_message) // 4 + len(SYSTEM_PROMPT) // 4
    completion_tokens = 0

    # Load past session turns from Redis / Memory
    past_turns = await load_session_history(session_id)
    history_contents = build_gemini_history(past_turns)

    if settings.GEMINI_API_KEY:
        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            config = types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=AVAILABLE_TOOLS,
                temperature=0.2
            )
            chat = client.chats.create(
                model=settings.GEMINI_MODEL,
                config=config,
                history=history_contents if history_contents else None
            )

            # Stage 1: Stream initial thoughts and collect requested function calls
            pending_fcalls = []
            in_thought_mode = False
            thought_buffer = ""

            response_stream = chat.send_message_stream(user_message)
            for chunk_obj in response_stream:
                if chunk_obj.function_calls:
                    pending_fcalls.extend(chunk_obj.function_calls)
                elif chunk_obj.candidates:
                    for cand in chunk_obj.candidates:
                        if cand.content and cand.content.parts:
                            for part in cand.content.parts:
                                if part.text:
                                    text_str = part.text
                                    thought_buffer += text_str

                                    if "THOUGHT:" in thought_buffer and not in_thought_mode:
                                        in_thought_mode = True
                                        thought_buffer = thought_buffer.split("THOUGHT:", 1)[1]

                                    if in_thought_mode:
                                        if "END_THOUGHT" in thought_buffer:
                                            thought_part, answer_part = thought_buffer.split("END_THOUGHT", 1)
                                            if thought_part.strip():
                                                yield format_sse("thought", {"token": "\n" + thought_part.strip()})
                                            in_thought_mode = False
                                            thought_buffer = ""
                                            if answer_part.strip():
                                                generated_text += answer_part.lstrip()
                                                yield format_sse("chunk", {"token": answer_part.lstrip()})
                                        else:
                                            yield format_sse("thought", {"token": "\n" + thought_buffer})
                                            thought_buffer = ""
                                    else:
                                        generated_text += text_str
                                        yield format_sse("chunk", {"token": text_str})

            # Stage 2: Execute requested tools against PostgreSQL and send tool responses back to Gemini
            if pending_fcalls:
                # Deduplicate requested tool calls so each distinct tool is executed once per turn
                seen_tools = set()
                unique_fcalls = []
                for fc in pending_fcalls:
                    if fc.name not in seen_tools:
                        seen_tools.add(fc.name)
                        unique_fcalls.append(fc)

                fn_parts = []
                for fcall in unique_fcalls:
                    tool_name = fcall.name
                    tool_args = fcall.args or {}
                    call_id = fcall.id or f"call_{int(time.time()*1000)}_{tool_name}"
                    
                    tool_calls_executed.append(tool_name)

                    # Append tool selection thought step
                    tool_thought = f"\nSelecting dynamic tool '{tool_name}' with parameters {json.dumps(tool_args)} to query PostgreSQL pgvector index."
                    yield format_sse("thought", {"token": tool_thought})
                    
                    yield format_sse("tool_start", {"tool": tool_name, "query": tool_args.get("query", user_message)})
                    yield format_sse("tool_call", {
                        "id": call_id,
                        "tool": tool_name,
                        "args": tool_args,
                        "status": "running"
                    })
                    
                    context, proj_slug, comp_slug, ui_act = await _execute_backend_tool(
                        tool_name, tool_args, user_message, db
                    )
                    
                    yield format_sse("tool_call", {
                        "id": call_id,
                        "tool": tool_name,
                        "args": tool_args,
                        "status": "completed",
                        "summary": context[:120] if context else ""
                    })

                    if ui_act:
                        yield format_sse("ui_action", ui_act)
                    elif proj_slug:
                        yield format_sse("ui_action", {"action": "navigate", "route": "/projects", "target": proj_slug})
                    elif comp_slug:
                        yield format_sse("ui_action", {"action": "navigate", "route": "/experience", "target": comp_slug})

                    fn_parts.append(
                        types.Part(
                            function_response=types.FunctionResponse(
                                name=tool_name,
                                response={"result": context}
                            )
                        )
                    )

                # Stage 3: Stream follow-up grounded response from Gemini
                followup_stream = chat.send_message_stream(fn_parts)
                for f_chunk in followup_stream:
                    if f_chunk.candidates:
                        for cand in f_chunk.candidates:
                            if cand.content and cand.content.parts:
                                for part in cand.content.parts:
                                    if part.text:
                                        generated_text += part.text
                                        yield format_sse("chunk", {"token": part.text})
                                        await asyncio.sleep(0.01)

        except Exception as e:
            print(f"Gemini agent loop error, using dynamic fallback: {e}")
            generated_text = ""

    # Graceful fallback path (if Gemini API key missing or error)
    if not generated_text:
        query_lower = user_message.lower()
        selected_tool = "search_all_entities"
        if "project" in query_lower:
            selected_tool = "search_projects"
        elif any(k in query_lower for k in ["experience", "work", "job", "intern", "company", "thuriyam", "iisc"]):
            selected_tool = "search_experiences"
        elif any(k in query_lower for k in ["faq", "rrf", "hnsw", "kafka", "celery", "tradeoff"]):
            selected_tool = "search_faqs"

        reasoning_fallback = f"Analyzing prompt intent ('{user_message[:50]}...'). Selecting dynamic tool '{selected_tool}' to query PostgreSQL HNSW vector index."
        yield format_sse("thought", {"token": reasoning_fallback})

        call_id = f"call_{int(time.time()*1000)}_{selected_tool}"
        yield format_sse("tool_start", {"tool": selected_tool, "query": user_message})
        yield format_sse("tool_call", {"id": call_id, "tool": selected_tool, "args": {"query": user_message}, "status": "running"})
        tool_calls_executed.append(selected_tool)

        context, proj_slug, comp_slug, ui_act = await _execute_backend_tool(selected_tool, {"query": user_message}, user_message, db)
        
        yield format_sse("tool_call", {"id": call_id, "tool": selected_tool, "args": {"query": user_message}, "status": "completed", "summary": context[:120]})

        if proj_slug:
            yield format_sse("ui_action", {"action": "navigate", "route": "/projects", "target": proj_slug})
        elif comp_slug:
            yield format_sse("ui_action", {"action": "navigate", "route": "/experience", "target": comp_slug})

        if context and context != "No matching entities found in database.":
            fallback_response = f"Based on Yogesh's portfolio database records:\n\n{context}\n\nYogesh Sharma is a 2026 IIT Jodhpur undergraduate specializing in Applied AI, High-Performance Systems, Vector DB Retrieval, and Distributed Architectures."
        else:
            fallback_response = "I am Yogesh's AI Technical Proxy! Ask me about Yogesh Sharma's engineering projects (like the Autonomous Portfolio Agent platform and Attentive Aggregation), work experience at Thuriyam AI, AI Stealth Startup, and IISc NLP Lab, or core system design trade-offs."

        words = fallback_response.split(" ")
        for i in range(0, len(words), 3):
            chunk_str = " ".join(words[i:i+3]) + " "
            generated_text += chunk_str
            yield format_sse("chunk", {"token": chunk_str})

    if generated_text.strip():
        await save_session_history(session_id, user_message, generated_text.strip())

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
