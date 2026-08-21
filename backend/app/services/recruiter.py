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

import json
from google.genai import types

async def analyze_job_description(
    raw_jd_text: str,
    company_name: str | None,
    target_role: str | None,
    session_id: str,
    db: AsyncSession
) -> Dict[str, Any]:
    """
    Parses JD text using Gemini LLM, evaluates match alignment against
    Yogesh's canonical tech stack & projects, computes fit score (0-100),
    extracts skill evidence & gaps, and saves document in MongoDB 'jd_analyses'.
    """
    # Fetch canonical skills & projects from Postgres for context grounding
    skills_res = await db.execute(select(Skill))
    skills = skills_res.scalars().all()
    canonical_tech = [s.name for s in skills]

    projects_res = await db.execute(select(Project))
    projects = projects_res.scalars().all()
    canonical_projects = [f"{p.title}: {p.tagline} (Problem: {p.problem_statement} | Solution: {p.solution_overview})" for p in projects]

    fit_score = 85.0
    extracted_tech_stack = []
    matched_skills: List[SkillAlignment] = []
    missing_gaps = []
    generated_pitch = ""

    # Attempt Gemini LLM structured JD alignment evaluation
    if settings.GEMINI_API_KEY:
        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            prompt = f"""You are an expert AI Recruiting & Systems Engineering Evaluator analyzing candidate alignment for Yogesh Sharma.
Compare the provided Job Description against Yogesh's actual technical background and portfolio records:

Candidate Background Context (Yogesh Sharma):
- Education: 2026 B.Tech from IIT Jodhpur (Minor in AI & Data Engineering).
- Canonical Tech Stack: {', '.join(canonical_tech)}
- Projects:
  {chr(10).join(['- ' + cp for cp in canonical_projects])}
- Work Experience:
  - Thuriyam AI (AI & Backend Engineer Intern): Architected async FastAPI microservices, PostgreSQL pgvector hybrid retrieval, Redis caching.
  - IISc Bangalore NLP Lab (Research Intern): Low-resource LLM fine-tuning, domain adaptation.
  - AI Stealth Startup (AI Software Engineer Intern): Production RAG pipelines, prompt engineering, agentic workflows.

Target Role: {target_role or 'Applied AI / Systems Engineer'}
Target Company: {company_name or 'Hiring Team'}

Job Description:
\"\"\"
{raw_jd_text}
\"\"\"

Task:
Respond ONLY with a valid raw JSON object matching this exact schema:
{{
  "fit_score": <float between 0.0 and 100.0>,
  "extracted_tech_stack": [<list of strings extracted from JD that match candidate skills>],
  "matched_skills": [
    {{
      "requirement": "<string describing JD requirement>",
      "matched_experience": "<string detailing candidate exact project or role match>",
      "confidence_score": <float between 0.5 and 1.0>,
      "evidence_source": "<string citing project or company name>"
    }}
  ],
  "missing_gaps": [<list of strings for technical requirements in JD where candidate has partial or no direct experience>],
  "generated_pitch": "<string containing a concise, 2-3 sentence recruiter pitch highlighting why candidate is ideal for this role>"
}}
"""
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )

            if response.text:
                parsed = json.loads(response.text)
                fit_score = float(parsed.get("fit_score", 85.0))
                extracted_tech_stack = parsed.get("extracted_tech_stack", [])
                
                raw_matched = parsed.get("matched_skills", [])
                for item in raw_matched:
                    matched_skills.append(
                        SkillAlignment(
                            requirement=item.get("requirement", ""),
                            matched_experience=item.get("matched_experience", ""),
                            confidence_score=float(item.get("confidence_score", 0.9)),
                            evidence_source=item.get("evidence_source", "Project: Autonomous Portfolio Agent")
                        )
                    )
                missing_gaps = parsed.get("missing_gaps", [])
                generated_pitch = parsed.get("generated_pitch", "")
        except Exception as e:
            print(f"Gemini JD analysis error, falling back to keyword baseline: {e}")

    # Baseline fallback if Gemini unavailable or failed
    if not matched_skills:
        jd_lower = raw_jd_text.lower()
        extracted_tech_stack = [tech for tech in canonical_tech if tech.lower() in jd_lower]
        fit_score = min(len(extracted_tech_stack) * 12.5 + 40.0, 96.0)

        for tech in extracted_tech_stack[:5]:
            matched_skills.append(
                SkillAlignment(
                    requirement=f"Experience with {tech}",
                    matched_experience=f"Architected production systems leveraging {tech} under high performance constraints.",
                    confidence_score=0.95,
                    evidence_source="Project: Autonomous Portfolio Agent"
                )
            )

        if "aws" in jd_lower or "kubernetes" in jd_lower:
            missing_gaps.append("Production AWS EKS cluster deployment (Self-hosted Docker Swarm / Compose used in core projects)")
        if "go" in jd_lower or "golang" in jd_lower:
            missing_gaps.append("Golang microservices (Primary expertise in Python / FastAPI & Async Systems)")

        generated_pitch = f"With proven experience architecting async FastAPI microservices, pgvector hybrid search, Redis sliding-window limiters, and Kafka event streaming pipelines, Yogesh Sharma is exceptionally well-equipped for the {target_role or 'Applied AI / Systems Engineer'} role at {company_name or 'your team'}."

    analysis_id = str(uuid.uuid4())
    doc = JobDescriptionAnalysisDocument(
        analysis_id=analysis_id,
        session_id=session_id,
        raw_jd_text=raw_jd_text,
        company_name=company_name,
        target_role=target_role,
        extracted_tech_stack=extracted_tech_stack,
        fit_score=round(fit_score, 1),
        matched_skills=matched_skills,
        missing_gaps=missing_gaps,
        generated_pitch=generated_pitch
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
