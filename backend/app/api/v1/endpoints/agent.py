import uuid
from fastapi import APIRouter, Depends, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.services.agent import stream_agent_chat

router = APIRouter(prefix="/agent", tags=["Agent"])


class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str


@router.post("/chat")
async def chat_agent(
    payload: ChatRequest = Body(...),
    db: AsyncSession = Depends(get_db)
):
    session_id = payload.session_id or str(uuid.uuid4())
    return StreamingResponse(
        stream_agent_chat(session_id=session_id, user_message=payload.message, db=db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
