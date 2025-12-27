"""
Week 3 - Exercise 2: Redis cache-aside (with safe fallback)

This file works without Redis installed by using an in-memory dict cache,
but also shows how you'd use redis-py if available.

Run:
  python python_expert_learning/week3/exercises/02_redis_cache_aside.py
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Optional


class InMemoryCache:
    def __init__(self) -> None:
        self._store: dict[str, tuple[float, str]] = {}

    def get(self, key: str) -> Optional[str]:
        item = self._store.get(key)
        if item is None:
            return None
        expires_at, value = item
        if expires_at < time.time():
            self._store.pop(key, None)
            return None
        return value

    def setex(self, key: str, ttl_seconds: int, value: str) -> None:
        self._store[key] = (time.time() + ttl_seconds, value)


def get_redis_client():
    """
    Optional: if redis is installed and REDIS_URL is set, you can connect for real.
    Otherwise we use an in-memory fallback.
    """
    try:
        import os
        import redis  # type: ignore

        url = os.getenv("REDIS_URL")
        if not url:
            return InMemoryCache()
        return redis.from_url(url, decode_responses=True)
    except Exception:
        return InMemoryCache()


@dataclass(frozen=True)
class UserProfile:
    user_id: str
    name: str
    plan: str


def db_fetch_user_profile(user_id: str) -> UserProfile:
    """
    Pretend DB call.
    TODO (you): replace with real DB query once you're ready.
    """
    time.sleep(0.05)  # simulate latency
    return UserProfile(user_id=user_id, name=f"user-{user_id}", plan="free")


def cache_key_user_profile(user_id: str) -> str:
    return f"user_profile:{user_id}"


def get_user_profile_cache_aside(cache, user_id: str, *, ttl_seconds: int = 30) -> UserProfile:
    key = cache_key_user_profile(user_id)
    cached = cache.get(key)
    if cached:
        data = json.loads(cached)
        return UserProfile(**data)

    # Cache miss -> fetch from DB -> populate cache
    profile = db_fetch_user_profile(user_id)
    cache.setex(key, ttl_seconds, json.dumps(profile.__dict__))
    return profile


def main() -> None:
    cache = get_redis_client()

    t0 = time.time()
    p1 = get_user_profile_cache_aside(cache, "42")
    t1 = time.time()
    p2 = get_user_profile_cache_aside(cache, "42")
    t2 = time.time()

    print("first:", p1, f"({(t1 - t0)*1000:.1f}ms)")
    print("second:", p2, f"({(t2 - t1)*1000:.1f}ms)")

    print("\n✅ Next steps (do these TODOs):")
    print("- Add TTL jitter (random +/- 10%)")
    print("- Add a per-key lock to prevent stampede (dogpile)")
    print("- Add explicit invalidation: cache.delete(key) on updates (Redis only)")


if __name__ == "__main__":
    main()


