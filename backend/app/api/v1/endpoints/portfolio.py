from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.sql_models import Project, Experience, Skill, SystemTradeoff

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


@router.get("/projects")
async def get_projects(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).order_by(Project.display_order.asc()))
    projects = result.scalars().all()
    return projects


@router.get("/experiences")
async def get_experiences(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Experience).order_by(Experience.start_date.desc()))
    experiences = result.scalars().all()
    return experiences


@router.get("/skills")
async def get_skills(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Skill))
    skills = result.scalars().all()
    return skills


@router.get("/tradeoffs")
async def get_tradeoffs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SystemTradeoff))
    tradeoffs = result.scalars().all()
    return tradeoffs
