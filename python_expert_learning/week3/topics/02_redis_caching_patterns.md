# Topic 2: Redis Caching Patterns (Python)

## 🎯 What you’ll learn

- When caching helps vs hurts
- The **cache-aside** pattern (most common)
- TTLs, invalidation, and “cache stampede” mitigation

## 1) When to use Redis

Good fits:

- **Hot reads**: same keys requested frequently
- **Expensive computation**: derived data, aggregation results
- **Rate limiting / counters**: fast atomic increments

Bad fits:

- Data that must be 100% fresh at all times
- Very large payloads (consider compression / alternative stores)

## 2) Cache-aside (read-through-ish)

Pseudocode:

1. Try cache
2. If miss: read DB
3. Populate cache with TTL
4. Return value

## 3) TTL + invalidation

Two strategies:

- **TTL-only**: simplest, eventual freshness
- **Explicit invalidation**: delete/update cache on writes (harder, more correct)

## 4) Cache stampede (dogpile) basics

Problem: popular key expires → many requests miss → DB gets hammered.

Mitigations:

- **Jitter** TTLs (randomize expiration)
- **Lock per key** (only one request recomputes)
- **Soft TTL** (serve stale + refresh async)

## ✅ Next: Hands-on exercise

Do: `python_expert_learning/week3/exercises/02_redis_cache_aside.py`


