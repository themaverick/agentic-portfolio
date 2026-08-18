from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.core.redis import check_rate_limit


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware applying Redis sliding-window rate limiting per IP address.
    """

    def __init__(
        self, app, limit: int = 10, window_seconds: int = 60
    ):
        super().__init__(app)
        self.limit = limit
        self.window_seconds = window_seconds

    async def dispatch(self, request: Request, call_next):
        # Exclude docs, health, telemetry stats, static options requests
        if request.url.path in ["/docs", "/openapi.json", "/health", "/api/v1/telemetry/stats"] or request.method == "OPTIONS":
            return await call_next(request)

        # Extract client IP
        client_ip = request.client.host if request.client else "127.0.0.1"
        client_hash = f"ip_{client_ip}"

        allowed, remaining, retry_after = await check_rate_limit(
            identifier=client_hash,
            limit=self.limit,
            window_seconds=self.window_seconds,
        )

        if not allowed:
            time_unit = f"{self.window_seconds // 60} minute(s)" if self.window_seconds >= 60 else f"{self.window_seconds} seconds"
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Limit is {self.limit} requests per {time_unit}.",
                    "retry_after_seconds": retry_after,
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.limit),
                    "X-RateLimit-Remaining": "0",
                },
            )

        response: Response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
