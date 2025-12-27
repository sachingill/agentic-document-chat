# Topic 4: PySpark Fundamentals (Python Big Data)

## 🎯 What you’ll learn

- Spark’s lazy evaluation model: **transformations vs actions**
- DataFrame basics: select/filter/groupBy
- Where performance goes: **shuffles**, partitioning, wide vs narrow transformations

## 1) Spark mental model

Spark is a distributed compute engine. Your Python code builds a **logical plan**.

- **Transformations** (lazy): `select`, `filter`, `withColumn`, `join`, `groupBy` (plan building)
- **Actions** (execute): `count`, `collect`, `show`, `write` (job runs)

## 2) Why “collect()” is dangerous

`collect()` pulls data back to the driver process. On big datasets, this can OOM your driver.

Prefer:

- `show(n)`
- `limit(n)`
- aggregate first, then `collect()`

## 3) Shuffles (the expensive step)

Operations like `groupBy` and many joins often require moving data across the cluster.

You’ll notice shuffles via:

- high runtime
- spilled disk usage
- big stage boundaries

## ✅ Next: Hands-on exercise

Do: `python_expert_learning/week3/exercises/04_pyspark_wordcount.py`


