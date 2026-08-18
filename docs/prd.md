# Product Requirements Document (PRD)

## 1. Purpose & Vision
The Autonomous Portfolio Agent is a dual-purpose platform: a polished portfolio showcase for recruiters and hiring managers, and a live demonstration of Applied AI/Full-Stack Systems engineering. It proves competence in polyglot persistence, hybrid search, distributed event streaming, and agentic tool use.

## 2. Target Personas
- **Technical Recruiter (Time: 30–60 seconds):** Needs instant qualification, tech stack verification, and low-friction contact capture.
- **Engineering Hiring Manager (Time: 3–10 minutes):** Evaluates system design trade-offs, architecture decisions, code quality, and production telemetry.
- **Peer Developer:** Explores project demos, UI interactions, and technical benchmarks.

## 3. Functional Requirements

### FR-1: Real-Time Conversational Agent
- Delivers an SSE-streamed interactive chat drawer available globally across all routes.
- Resolves portfolio questions factually using Hybrid Search over PostgreSQL (`pgvector` + FTS).
- Orchestrates the UI dynamically by emitting navigation and highlighting events.

### FR-2: Recruiter Alignment & Job Description Analyzer
- Accepts raw pasted Job Description (JD) text up to 10,000 characters.
- Extracts engineering requirements, cross-references internal skills records, and outputs a 0–100 match score with cited evidence and identified gaps.
- Persists extraction results in MongoDB (`jd_analyses`) and generates a custom elevator pitch.

### FR-3: Architectural Trade-Off Inspector
- Serves verified architectural rationales for key decisions (e.g., Kafka vs. Celery, Redis sliding window vs. token bucket, HNSW vs. IVFFlat).

### FR-4: Lead Capture & Instant Notification
- Captures recruiter name, company, email, salary range, and custom notes.
- Persists leads ACID-compliantly in PostgreSQL and triggers instant alerts via Kafka to Discord/Email.

### FR-5: Public Telemetry Dashboard
- Ingests streaming metrics (latencies, token counts, tool calls) via Kafka to MongoDB.
- Exposes aggregated p50/p95/p99 latency percentiles and token volume over 7d/30d windows.

## 4. Non-Functional Requirements
- **Cost:** $0.00 infrastructure cost using Google AI Studio (Gemini 2.5 Flash free tier) and self-hosted Docker components.
- **Availability & Degradation:** Graceful fallback to static keyword search if Gemini free quota limits are triggered.
- **Performance:** Time-to-First-Token (TTFT) < 1.5s on agent responses; search execution < 25ms.
- **Rate Limit:** 10 requests per 10-minute sliding window per IP address for anonymous visitors.