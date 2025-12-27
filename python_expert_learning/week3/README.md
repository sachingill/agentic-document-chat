# 🧩 Week 3: Integrations (Databases, Caching, Streaming, Spark)

Week 3 is about **building real systems with Python** by integrating with the common building blocks you’ll see in production:

- **Databases**: MySQL / PostgreSQL (SQL fundamentals + Python DB access patterns)
- **Caching**: Redis (cache-aside, TTLs, stampede control)
- **Streaming**: Kafka (producer/consumer mental model, idempotency, offsets)
- **Big Data**: PySpark (DataFrames, transformations vs actions, partitioning basics)

## 📌 Goal

By the end of this week, you should be able to:

- Write Python code that **talks to SQL databases** safely (transactions, parameterization)
- Use **Redis** to reduce latency and protect databases
- Model work as **events** and process them safely (at-least-once, idempotency)
- Run a **small Spark job** and explain what happens (lazy evaluation, shuffles)

## 🧰 Prerequisites (optional installs)

These topics can be learned even without installing anything (we provide fallbacks), but to run the “real integration” paths you’ll want:

- SQL toolkit: `sqlalchemy`
- Postgres driver: `psycopg` (or `psycopg2`)
- MySQL driver: `pymysql` (or `mysqlclient`)
- Redis client: `redis`
- Kafka client: `kafka-python` (or `confluent-kafka`)
- Spark: `pyspark`

## 🚀 Start here

Open: `python_expert_learning/week3/START_HERE.md`


