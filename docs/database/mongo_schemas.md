# MongoDB Document Schemas & Collections

## 1. Pydantic v2 Models (`backend/app/schemas/mongo_models.py`)

```python
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ToolInvocation(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    execution_time_ms: float
    status: str = "SUCCESS"


class ChatMessage(BaseModel):
    message_id: str
    role: str  # 'user' | 'assistant' | 'system' | 'tool'
    content: str
    tool_calls: Optional[List[ToolInvocation]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ChatSessionDocument(BaseModel):
    session_id: str
    client_fingerprint: str
    ip_hash: str
    auth_tier: str = "anonymous"
    messages: List[ChatMessage] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SkillAlignment(BaseModel):
    requirement: str
    matched_experience: str
    confidence_score: float
    evidence_source: str


class JobDescriptionAnalysisDocument(BaseModel):
    analysis_id: str
    session_id: str
    raw_jd_text: str
    company_name: Optional[str] = None
    target_role: Optional[str] = None
    extracted_tech_stack: List[str] = []
    fit_score: float
    matched_skills: List[SkillAlignment] = []
    missing_gaps: List[str] = []
    generated_pitch: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TelemetryLogDocument(BaseModel):
    event_id: str
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    endpoint: str
    model_version: str = "gemini-2.5-flash"
    latency_breakdown: Dict[str, float]
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    tool_calls_executed: List[str]
    cache_hit: bool = False
    status_code: int = 200