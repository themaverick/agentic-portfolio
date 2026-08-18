from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.mongo import close_mongo_connection
from app.core.kafka import stop_kafka_producer
from app.middleware.rate_limit import RateLimitMiddleware

from app.api.v1.endpoints.agent import router as agent_router
from app.api.v1.endpoints.recruiter import router as recruiter_router
from app.api.v1.endpoints.telemetry import router as telemetry_router
from app.api.v1.endpoints.portfolio import router as portfolio_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    print(f"Starting Autonomous Portfolio Agent Backend in {settings.ENVIRONMENT} mode...")
    yield
    # Shutdown actions
    await close_mongo_connection()
    await stop_kafka_producer()
    print("Backend resources cleaned up successfully.")


app = FastAPI(
    title="Autonomous Portfolio Agent API",
    description="Polyglot Backend API providing Hybrid Vector Search, SSE Agent Chat, Recruiter Alignment, and Distributed Telemetry",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sliding-Window Rate Limiting Middleware
app.add_middleware(
    RateLimitMiddleware,
    limit=10,
    window_seconds=60
)

# Include Routers
app.include_router(agent_router, prefix="/api/v1")
app.include_router(recruiter_router, prefix="/api/v1")
app.include_router(telemetry_router, prefix="/api/v1")
app.include_router(portfolio_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0"
    }
