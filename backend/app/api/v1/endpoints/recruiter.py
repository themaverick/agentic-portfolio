import uuid
from fastapi import APIRouter, Depends, Body, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr

from app.core.database import get_db
from app.services.recruiter import analyze_job_description, capture_lead

router = APIRouter(prefix="/recruiter", tags=["Recruiter"])


class JDAnalysisRequest(BaseModel):
    session_id: str | None = None
    raw_jd_text: str
    company_name: str | None = None
    target_role: str | None = None


class LeadCaptureRequest(BaseModel):
    recruiter_name: str
    company: str
    email: str
    linkedin_url: str | None = None
    message: str | None = None
    salary_band: str | None = None


@router.post("/analyze-jd")
async def api_analyze_jd(
    payload: JDAnalysisRequest = Body(...),
    db: AsyncSession = Depends(get_db)
):
    if len(payload.raw_jd_text.strip()) < 10:
        raise HTTPException(status_code=400, detail="Job description text too short.")

    session_id = payload.session_id or str(uuid.uuid4())
    result = await analyze_job_description(
        raw_jd_text=payload.raw_jd_text,
        company_name=payload.company_name,
        target_role=payload.target_role,
        session_id=session_id,
        db=db
    )
    return result


@router.post("/lead", status_code=201)
async def api_capture_lead(
    payload: LeadCaptureRequest = Body(...),
    db: AsyncSession = Depends(get_db)
):
    result = await capture_lead(
        recruiter_name=payload.recruiter_name,
        company=payload.company,
        email=payload.email,
        linkedin_url=payload.linkedin_url,
        message=payload.message,
        salary_band=payload.salary_band,
        db=db
    )
    return result
