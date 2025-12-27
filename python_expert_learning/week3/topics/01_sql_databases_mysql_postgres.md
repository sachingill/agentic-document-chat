# Topic 1: SQL Databases with Python (PostgreSQL + MySQL)

## 🎯 What you’ll learn

- How to think about **SQL** as sets + indexes + transactions
- The Python DB “stack”:
  - **Driver** (talks to DB): Postgres/MySQL drivers
  - **SQL toolkit/ORM** (optional): SQLAlchemy
- Production basics: **parameterized queries**, **transactions**, **pooling**, **migrations mindset**

## 1) SQL basics that matter in production

- **SELECT**: filter + project columns (avoid `SELECT *` in hot paths)
- **WHERE**: use indexes; avoid functions on indexed columns (`LOWER(email)` can disable index unless you design for it)
- **JOIN**: understand cardinality; join order can matter
- **ORDER BY / LIMIT**: paging is easy, but be careful with deep offsets
- **Indexes**: speed reads, slow writes; design based on query patterns

## 2) Python database access patterns

### Pattern A — Driver-only (direct SQL)

- Pros: explicit, fast, simple
- Cons: more boilerplate

Key rule: **never string-concatenate user input into SQL**.

### Pattern B — SQLAlchemy Core/ORM

- Pros: portability, pooling, composition
- Cons: abstraction costs; you still need SQL understanding

## 3) Transactions (the “unit of correctness”)

Treat a transaction as:

- **Start**: “my view of the world”
- **Work**: one or more reads/writes
- **Commit**: “make it true”
- **Rollback**: “pretend it never happened”

In Python: always ensure commit/rollback happens even on exceptions.

## 4) Pooling (performance + reliability)

Opening DB connections is expensive.

- Use a **connection pool** (SQLAlchemy provides one)
- Avoid “connect-per-request” in high-throughput services

## 5) Common production pitfalls

- **N+1 queries**: many small queries instead of one join
- **No timeouts**: hung queries pile up
- **No retries**: transient network errors become outages
- **No idempotency**: retries can double-write

## ✅ Next: Hands-on exercise

Do: `python_expert_learning/week3/exercises/01_sql_foundations_sqlite_first.py`

This exercise starts with built-in `sqlite3` so it runs anywhere, then shows how you’d switch to Postgres/MySQL.


