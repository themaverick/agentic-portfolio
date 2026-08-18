# SSD 01: Real-Time Agent Chat & Hybrid Retrieval

## 1. Flow Diagram

```mermaid
sequenceDiagram
    autonumber
    actor Recruiter as Recruiter (React UI)
    participant Gateway as FastAPI Gateway
    participant Redis as Redis Cache
    participant Gemini as Gemini 2.5 Flash
    participant PG as PostgreSQL (pgvector)
    participant Kafka as Apache Kafka

    Recruiter->>Gateway: POST /api/v1/agent/chat (SSE Stream)
    Gateway->>Redis: Check Sliding-Window Rate Limit (ZADD / ZCARD)
    Redis-->>Gateway: OK (Within 10 req/10 min)
    Gateway->>Redis: Fetch Active Session Context
    Redis-->>Gateway: Return Session History
    Gateway-->>Recruiter: SSE event: handshake
    Gateway->>Gemini: Stream Generation (Prompt + History + Tools)
    Gemini-->>Gateway: ToolCall: search_portfolio_hybrid(query)
    Gateway-->>Recruiter: SSE event: tool_start
    Gateway->>PG: match_portfolio_hybrid(query, embedding) [HNSW + FTS + RRF]
    PG-->>Gateway: Top-K Ranked Chunks
    Gateway->>Gemini: Feed Tool Output
    Gemini-->>Gateway: ToolCall: navigate_ui(route, target_id)
    Gateway-->>Recruiter: SSE event: ui_action
    Gemini-->>Gateway: Text Tokens Stream
    Gateway-->>Recruiter: SSE event: chunk
    Gemini-->>Gateway: Finish: STOP
    Gateway-->>Recruiter: SSE event: done
    Gateway-)Kafka: Produce Event (Topic: 'agent-telemetry')
```

## 2. API Contract & Payloads
- **Endpoint:** `POST /api/v1/agent/chat`
- **Request Body:**
  ```json
  {
    "session_id": "UUID",
    "message": "string"
  }
  ```
- **SSE Events Emitted:** `handshake`, `tool_start`, `ui_action`, `chunk`, `error`, `done`.