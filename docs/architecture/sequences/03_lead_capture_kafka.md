# SSD 03: Lead Capture & Asynchronous Kafka Alert Pipeline

## 1. Flow Diagram

```mermaid
sequenceDiagram
    autonumber
    actor Client as Recruiter / Agent Tool
    participant Gateway as FastAPI Gateway
    participant PG as PostgreSQL (ACID DB)
    participant Kafka as Apache Kafka Broker
    participant Worker as Alert Consumer Worker
    participant Discord as Discord Webhook API

    Client->>Gateway: POST /api/v1/recruiter/lead (or Tool Call)
    
    rect rgb(240, 248, 255)
        Note over Gateway,PG: ACID Transaction Boundary
        Gateway->>PG: BEGIN TRANSACTION
        Gateway->>PG: INSERT INTO recruiter_leads (...) VALUES (...) RETURNING id;
        PG-->>Gateway: Row Created (lead_id: UUID)
        Gateway->>PG: COMMIT
        PG-->>Gateway: Transaction Committed
    end
    
    Gateway-)Kafka: Produce Message (Topic: 'recruiter-leads', Key: lead_id)
    Kafka-->>Gateway: ACK (TopicPartition: 0, Offset: 1042)
    Gateway-->>Client: 201 Created (lead_id, status: "SUBMITTED")

    Note over Kafka,Worker: Decoupled Asynchronous Processing
    Kafka->>Worker: Consume Message (lead_id, name, email, company, message)
    Worker->>Discord: POST /api/webhooks/... (Rich Alert Embed)
    Discord-->>Worker: 204 No Content
    Worker->>Kafka: Commit Offset (Offset: 1042)
```

## 2. Event & Message Schemas

### Kafka Topic: `recruiter-leads`
- **Partition Key:** `lead_id` (UUID string)
- **Payload Schema:**
```json
{
  "event_id": "a6b7c8d9-0123-4567-89ab-cdef01234567",
  "lead_id": "550e8400-e29b-41d4-a716-446655440000",
  "recruiter_name": "Jane Smith",
  "company": "Vertex AI Labs",
  "email": "jane.smith@vertex.io",
  "linkedin_url": "[https://linkedin.com/in/janesmith](https://linkedin.com/in/janesmith)",
  "message": "Loved the hybrid search implementation. Would like to set up a technical interview.",
  "salary_band": "$160,000 - $190,000 USD",
  "timestamp": "2026-08-17T17:48:55Z"
}
```

### Discord Outbound Webhook Embed
```json
{
  "username": "Portfolio Lead Bot",
  "avatar_url": "[https://raw.githubusercontent.com/user/portfolio/main/public/bot-avatar.png](https://raw.githubusercontent.com/user/portfolio/main/public/bot-avatar.png)",
  "embeds": [
    {
      "title": "🚨 New Recruiter Lead Captured!",
      "color": 5814783,
      "fields": [
        { "name": "Recruiter", "value": "Jane Smith", "inline": true },
        { "name": "Company", "value": "Vertex AI Labs", "inline": true },
        { "name": "Email", "value": "jane.smith@vertex.io", "inline": false },
        { "name": "Salary Band", "value": "$160k - $190k", "inline": true },
        { "name": "Message", "value": "Loved the hybrid search implementation...", "inline": false }
      ],
      "footer": { "text": "Lead ID: 550e8400-e29b-41d4-a716-446655440000" },
      "timestamp": "2026-08-17T17:48:55Z"
    }
  ]
}
```