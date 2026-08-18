import time
from typing import Tuple
import redis.asyncio as aioredis
from app.core.config import settings

redis_client: aioredis.Redis = None

SLIDING_WINDOW_LUA = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local clearBefore = now - window

redis.call('ZREMRANGEBYSCORE', key, '-inf', clearBefore)
local currentRequests = redis.call('ZCARD', key)

if currentRequests < limit then
    redis.call('ZADD', key, now, now)
    redis.call('PEXPIRE', key, window)
    return {1, limit - currentRequests - 1, 0}
else
    local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
    local retryAfter = math.ceil((tonumber(oldest[2]) + window - now) / 1000)
    return {0, 0, math.max(retryAfter, 1)}
end
"""

_rate_limit_script = None


def get_redis() -> aioredis.Redis:
    global redis_client
    if redis_client is None:
        redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return redis_client


async def check_rate_limit(
    identifier: str, limit: int = 10, window_seconds: int = 600
) -> Tuple[bool, int, int]:
    """
    Evaluates sliding-window rate limit using Lua script in Redis.
    Returns: (is_allowed: bool, remaining_requests: int, retry_after_seconds: int)
    """
    global _rate_limit_script
    r = get_redis()
    if _rate_limit_script is None:
        _rate_limit_script = r.register_script(SLIDING_WINDOW_LUA)

    key = f"ratelimit:{identifier}"
    now_ms = int(time.time() * 1000)
    window_ms = window_seconds * 1000

    try:
        res = await _rate_limit_script(keys=[key], args=[now_ms, window_ms, limit])
        allowed, remaining, retry_after = res[0], res[1], res[2]
        return bool(allowed), int(remaining), int(retry_after)
    except Exception as e:
        # Fallback in case Redis connection is down in development
        print(f"Redis rate limit check error: {e}")
        return True, limit, 0
