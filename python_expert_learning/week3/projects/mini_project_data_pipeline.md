# 🏗️ Mini Project: Data Pipeline (SQL + Cache + Events + Batch)

## 🎯 What you’re building

A tiny “production-shaped” pipeline you can run locally (with fallbacks):

- Event ingestion (Kafka-like local bus)
- SQL persistence (sqlite3 first)
- Redis caching (in-memory fallback)
- Batch summary (PySpark if available, pure Python fallback)

## ✅ Step 1 — Event ingestion

Start from:

- `python_expert_learning/week3/exercises/03_event_bus_kafka_like.py`

Modify it so events represent page views:

- `{"user_id": "...", "path": "...", "ts": ...}`

## ✅ Step 2 — Persist events to SQL

Use sqlite3 patterns from:

- `python_expert_learning/week3/exercises/01_sql_foundations_sqlite_first.py`

Create a table:

- `pageviews(id, event_id, user_id, path, ts)`

Important:

- Enforce idempotency via a unique constraint on `event_id`.

## ✅ Step 3 — Cache hot aggregates

Use cache-aside from:

- `python_expert_learning/week3/exercises/02_redis_cache_aside.py`

Cache example:

- `pageviews_count:user:<user_id>` → integer

## ✅ Step 4 — Batch summary

Use:

- `python_expert_learning/week3/exercises/04_pyspark_wordcount.py`

Instead of word count, compute:

- pageviews per user
- top 3 paths

## ✅ Deliverable

Write a short README section in `python_expert_learning/SUMMARY.md` describing:

- your schema
- your idempotency strategy
- your cache key strategy + TTL choice
- your batch job output


