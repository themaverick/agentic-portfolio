import sys
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Add backend directory to sys.path for Vercel serverless deployment
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

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
origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=False if "*" in origins else True,
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


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    import traceback
    return JSONResponse(
        status_code=500,
        content={
            "error": str(exc),
            "type": exc.__class__.__name__,
            "traceback": traceback.format_exc(),
        },
    )
