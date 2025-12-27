# Topic 5: Mini Project — Data Pipeline (DB + Cache + Events + Batch)

## 🎯 Goal

Design a tiny “production-shaped” pipeline:

- **Ingest events** (Kafka-like interface)
- **Persist** events into a SQL database
- **Cache** hot aggregates in Redis (or an in-memory fallback)
- **Batch compute** a summary (PySpark if available, pure Python fallback otherwise)

## Architecture sketch (conceptual)

1. Producer emits events (e.g., page views)
2. Consumer reads events and writes to DB
3. API layer reads aggregate from cache; falls back to DB and warms cache
4. Batch job computes daily summary

## ✅ Build

Open: `python_expert_learning/week3/projects/mini_project_data_pipeline.md`


