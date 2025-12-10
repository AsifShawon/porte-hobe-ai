"""Rate limiter for FastAPI.

- Uses Redis (if REDIS_URL is set) for multi-instance setups.
- Falls back to an in-memory fixed window limiter otherwise.
"""
from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Deque, Dict
import os

_REDIS_URL = os.getenv("REDIS_URL")
_redis = None
if _REDIS_URL:
    try:  # lazy import
        import redis  # type: ignore
        _redis = redis.Redis.from_url(_REDIS_URL)
    except Exception:
        _redis = None

from fastapi import Depends, HTTPException, status

from auth import get_current_user


class FixedWindowLimiter:
    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window = window_seconds
        self.buckets: Dict[str, Deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        now = time.time()
        q = self.buckets[key]
        # drop old entries
        while q and now - q[0] > self.window:
            q.popleft()
        if len(q) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please slow down.",
            )
        q.append(now)


_memory_limiter = FixedWindowLimiter(max_requests=20, window_seconds=60)  # 20 req/min


def limit_user(user) -> None:
    """FastAPI dependency that rate-limits based on authenticated user.
    
    Args:
        user: Either a user dict with 'user_id' key, or a string user_id directly
    """
    # Handle both dict and string inputs
    if isinstance(user, str):
        user_id = user
    elif isinstance(user, dict):
        user_id = user.get("user_id", user.get("id", "anonymous"))
    else:
        user_id = "anonymous"
        
    if _redis is None:
        _memory_limiter.check(user_id)
        return
    # Redis fixed window: INCR with TTL
    key = f"rl:{user_id}"
    try:
        count = _redis.incr(key)
        if count == 1:
            _redis.expire(key, 60)
        if count > 20:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please slow down.",
            )
    except Exception:
        # On Redis failure, fall back to memory limiter
        _memory_limiter.check(user_id)
