from fastapi import APIRouter, Query
from app.services.telemetry import get_telemetry_stats

router = APIRouter(prefix="/telemetry", tags=["Telemetry"])


@router.get("/stats")
async def api_get_telemetry_stats(timeframe_days: int = Query(default=30, ge=1, le=365)):
    stats = await get_telemetry_stats(timeframe_days=timeframe_days)
    return stats
