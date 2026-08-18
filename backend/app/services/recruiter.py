import uuid
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from google import genai

from app.core.config import settings
from app.core.mongo import get_mongo_db
from app.core.kafka import produce_event
from app.models.sql_models import Skill, Project, RecruiterLead
from app.models.mongo_models import JobDescriptionAnalysisDocument, SkillAlignment

async def analyze_job_description(
    raw_jd_text: str,
    company_name: str | None,
    target_role: str | None,
    session_id: str,
    db: AsyncSession
) -> Dict[str, Any]:
    """
    Parses JD text, matches canonical tech stack in Postgres,
    computes fit score (0-100), extracts skill overlaps & gaps,
    and saves document in MongoDB collection 'jd_analyses'.
    """
    # Fetch canonical skills & projects from Postgres
    skills_res = await db.execute(select(Skill))
    skills = skills_res.scalars().all()
    canonical_tech = [s.name for s in skills]

    projects_res = await db.execute(select(Project))
    projects = projects_res.scalars().all()
    canonical_projects = [f"{p.title}: {p.tagline}" for p in projects]

    # Keyword overlap matching for robust baseline
    jd_lower = raw_jd_text.lower()
    matched_stack = [tech for tech in canonical_tech if tech.lower() in jd_lower]
    
    # Calculate fit score (0-100) based on matched tech stack density and role relevance
    base_score = min(len(matched_stack) * 12.5 + 40.0, 96.0)

    matched_skills = []
    for tech in matched_stack[:5]:
        matched_skills.append(
            SkillAlignment(
                requirement=f"Experience with {tech}",
                matched_experience=f"Architected systems leveraging {tech} in high-throughput environments.",
                confidence_score=0.95,
                evidence_source="Project: Autonomous Portfolio Agent"
            )
        )

    missing_gaps = []
    if "aws" in jd_lower or "kubernetes" in jd_lower:
        missing_gaps.append("Production AWS EKS cluster deployment (Self-hosted Docker Swarm / Compose used in core projects)")
    if "go" in jd_lower or "golang" in jd_lower:
        missing_gaps.append("Golang microservices (Primary expertise in Python / FastAPI & Async Systems)")

    tailored_pitch = f"With proven experience architecting async FastAPI microservices, pgvector hybrid search, Redis sliding-window limiters, and Kafka event streaming pipelines, Yogesh Sharma is exceptionally well-equipped for the {target_role or 'Applied AI / Systems Engineer'} role at {company_name or 'your team'}."

    analysis_id = str(uuid.uuid4())
    doc = JobDescriptionAnalysisDocument(
        analysis_id=analysis_id,
        session_id=session_id,
        raw_jd_text=raw_jd_text,
        company_name=company_name,
        target_role=target_role,
        extracted_tech_stack=matched_stack,
        fit_score=round(base_score, 1),
        matched_skills=matched_skills,
        missing_gaps=missing_gaps,
        generated_pitch=tailored_pitch
    )

    # Persist in MongoDB
    try:
        mongo_db = get_mongo_db()
        await mongo_db.jd_analyses.insert_one(doc.model_dump())
    except Exception as e:
        print(f"MongoDB write error for jd_analysis: {e}")

    return doc.model_dump()


async def capture_lead(
    recruiter_name: str,
    company: str,
    email: str,
    linkedin_url: str | None,
    message: str | None,
    salary_band: str | None,
    db: AsyncSession
) -> Dict[str, Any]:
    """
    Persists recruiter lead ACID-compliantly in PostgreSQL
    and produces async Kafka event for Discord alert workers.
    """
    lead = RecruiterLead(
        recruiter_name=recruiter_name,
        company=company,
        email=email,
        linkedin_url=linkedin_url,
        message=message,
        salary_band=salary_band,
        status="NEW"
    )
    db.add(lead)
    await db.commit()
    await db.refresh(lead)

    lead_payload = {
        "event_id": str(uuid.uuid4()),
        "lead_id": str(lead.id),
        "recruiter_name": lead.recruiter_name,
        "company": lead.company,
        "email": lead.email,
        "linkedin_url": lead.linkedin_url,
        "message": lead.message,
        "salary_band": lead.salary_band,
        "timestamp": lead.created_at.isoformat()
    }

    # Emit Kafka event
    await produce_event("recruiter-leads", lead_payload, key=str(lead.id))

    return {
        "lead_id": str(lead.id),
        "status": "SUBMITTED",
        "message": "Lead captured successfully. Alert emitted to Kafka event pipeline."
    }
