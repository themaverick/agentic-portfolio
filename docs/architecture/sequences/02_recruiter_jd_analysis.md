# SSD 02: Recruiter Job Description Fit Analysis & Gap Extraction

## 1. Flow Diagram

```mermaid
sequenceDiagram
    autonumber
    actor Recruiter as Recruiter (React UI)
    participant Gateway as FastAPI Gateway
    participant PG as PostgreSQL Core DB
    participant Gemini as Gemini 2.5 Flash
    participant Mongo as MongoDB Store

    Recruiter->>Gateway: POST /api/v1/recruiter/analyze-jd
    Note over Gateway: Validate payload & session
    Gateway->>PG: SELECT * FROM skills; SELECT * FROM projects;
    PG-->>Gateway: Canonical Experience & Skills Taxonomy
    
    Gateway->>Gemini: generate_content(JD_Text, Candidate_Profile, Schema)
    Note over Gemini: Enforce JSON Schema Output<br/>(Extract Tech, Match Overlaps, Calc Fit %, Identify Gaps)
    Gemini-->>Gateway: Validated Structured JSON Payload
    
    Gateway->>Mongo: Insert Document (Collection: 'jd_analyses')
    Mongo-->>Gateway: Write Result (Acknowledged, ObjectId)
    
    Gateway-->>Recruiter: 200 OK (Analysis ID, Fit Score, Matches, Pitch)
    Note over Recruiter: UI renders radar alignment chart<br/>and custom pitch card
```

## 2. API Contract & Payloads

### Endpoint
`POST /api/v1/recruiter/analyze-jd`

### Request Payload
```json
{
  "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "raw_jd_text": "We are seeking a Senior AI Systems Engineer with deep expertise in Python, FastAPI, Apache Kafka, and PostgreSQL with pgvector...",
  "company_name": "Acme Corp",
  "target_role": "Senior Applied AI Engineer"
}
```

### Response Payload (`200 OK`)
```json
{
  "analysis_id": "550e8400-e29b-41d4-a716-446655440000",
  "company_name": "Acme Corp",
  "target_role": "Senior Applied AI Engineer",
  "fit_score": 93.5,
  "matched_skills": [
    {
      "requirement": "FastAPI asynchronous microservices",
      "matched_experience": "Architected low-latency SSE gateway with Redis sliding-window limiters.",
      "confidence_score": 0.98,
      "evidence_source": "Project: Autonomous Portfolio Agent"
    },
    {
      "requirement": "Event-driven architecture with Kafka",
      "matched_experience": "Implemented decoupled telemetry streaming and alert workers.",
      "confidence_score": 0.95,
      "evidence_source": "Experience: AI Systems Engineer"
    }
  ],
  "missing_gaps": [
    "AWS EKS deployment (Self-hosted Docker Swarm used in core projects)"
  ],
  "tailored_pitch": "With proven experience designing async FastAPI gateways, hybrid search with pgvector, and scalable Kafka telemetry pipelines, I can hit the ground running on Acme Corp's AI infrastructure...",
  "created_at": "2026-08-17T17:48:55Z"
}
```