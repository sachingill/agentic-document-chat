# ✅ 10-Day Python Practical Plan (2–3 hrs/day)

This plan uses the **existing** `python_expert_learning/` curriculum, with a small amount of **new Week 2 content** (added alongside this plan) so you can build real skill in 10 days.

## How to use this plan (daily)
- **Read (20–30 min)**: one topic file.
- **Build (75–120 min)**: implement TODOs / run code / write tests.
- **Review (15–30 min)**: refactor + notes in `python_expert_learning/week1/notes/notes.txt` (or `week2/notes/` later).

## Day 0 (setup — 15 minutes)
- Open: `python_expert_learning/week1/START_HERE.md`
- Sanity run a file:
  - Run: `python python_expert_learning/week1/exercises/memory_profile.py`
  - If you hit missing deps, install from repo root: `pip install -r requirements.txt`

---

## Day 1 — Memory profiling fundamentals
- **Read**
  - `python_expert_learning/week1/topics/01_memory_profiling.md`
  - `python_expert_learning/week1/topics/00_tracemalloc_vs_profile.md`
- **Do**
  - In `python_expert_learning/week1/exercises/01_memory_profiling_exercises.py`:
    - Finish `exercise_1_profile()` and **fix** `process_data_inefficient()` (remove the leak).
    - Add quick asserts for correctness.
- **Problem practice (30 min)**
  - `python_expert_learning/week1/problems/01_two_sum.py`

## Day 2 — Generators + file processing
- **Read**
  - `python_expert_learning/week1/topics/00_generators_how_to_use.md`
  - `python_expert_learning/week1/topics/00_using_file_for_paths.md`
- **Do**
  - Implement `load_file_generator()` in `week1/exercises/01_memory_profiling_exercises.py`
  - Write a tiny script snippet that:
    - counts lines
    - finds lines matching a prefix
    - never loads the whole file into memory
- **Problem practice (30–45 min)**
  - Solve **Valid Anagram** (new file added by this plan): `python_expert_learning/week1/problems/02_valid_anagram.py`

## Day 3 — Chunking + Pandas memory tuning
- **Read**
  - `python_expert_learning/week1/topics/00_tracemalloc_vs_profile.md` (re-skim, focus on “when to use which”)
  - `python_expert_learning/week1/topics/00_memory_leaks_explained.md`
- **Do**
  - Implement `process_csv_chunked()` in `week1/exercises/01_memory_profiling_exercises.py`
  - Implement `create_dataframe_optimized()` in `week1/exercises/01_memory_profiling_exercises.py`
  - Measure memory usage before/after (print MB; note results).
- **Problem practice (30–45 min)**
  - Solve **Contains Duplicate**: `python_expert_learning/week1/problems/03_contains_duplicate.py`

## Day 4 — NumPy memory + feature engineering pipeline
- **Read**
  - `python_expert_learning/week1/topics/00_tracemalloc_vs_profile.md` (example section)
- **Do**
  - Implement `create_features_optimized()` in `week1/exercises/01_memory_profiling_exercises.py` (pre-allocate + `float32`)
  - Implement `feature_engineering_pipeline_optimized()` in `week1/exercises/01_memory_profiling_exercises.py` (chunking + dtypes)
- **Problem practice (30–45 min)**
  - Solve **Best Time to Buy and Sell Stock**: `python_expert_learning/week1/problems/04_best_time_stock.py`

---

## Day 5 — Concurrency: threading vs multiprocessing (and the GIL)
- **Read**
  - `python_expert_learning/week2/topics/01_threading_vs_multiprocessing.md`
  - `python_expert_learning/week2/topics/02_gil_primer.md`
- **Do**
  - Complete: `python_expert_learning/week2/exercises/01_concurrency_basics.py`
  - Run it and record:
    - IO-bound speedup (threading)
    - CPU-bound behavior (multiprocessing)
- **Problem practice (30–45 min)**
  - Solve **Valid Palindrome**: `python_expert_learning/week1/problems/05_valid_palindrome.py`

## Day 6 — Asyncio fundamentals (real IO)
- **Read**
  - `python_expert_learning/week2/topics/03_asyncio_basics.md`
- **Do**
  - Complete: `python_expert_learning/week2/exercises/02_asyncio_url_checker.py`
  - Make it print a summary: total URLs, ok/failed, p50/p95 latency (rough).
- **Problem practice (30–45 min)**
  - Solve **Two Sum II (sorted input)**: `python_expert_learning/week1/problems/06_two_sum_ii.py`

## Day 7 — Testing + profiling “done right”
- **Read**
  - `python_expert_learning/week2/topics/04_testing_with_pytest.md`
- **Do**
  - Add tests for one of your Week 2 exercises using `pytest`
  - Add a regression test for a memory leak pattern (bounded cache / LRU).
- **Problem practice (30–60 min)**
  - Solve **Longest Substring Without Repeating Characters**: `python_expert_learning/week1/problems/07_longest_substring_no_repeat.py`

## Day 8 — Mini-project: async health checker (practical)
- **Build**
  - Implement: `python_expert_learning/week2/projects/async_health_checker.py`
  - Requirements:
    - concurrency limit
    - timeout
    - retries (small)
    - JSON output
- **Problem practice (30–60 min)**
  - Solve **Product of Array Except Self**: `python_expert_learning/week1/problems/08_product_except_self.py`

## Day 9 — Performance pass + refactor day
- **Do**
  - Pick 2 files you wrote in the last 8 days and:
    - refactor into clean functions
    - add type hints
    - add tests
    - run a quick profile (time + memory)
- **Problem practice (45–75 min)**
  - Solve **3Sum**: `python_expert_learning/week1/problems/09_three_sum.py`

## Day 10 — “Expert-mode” consolidation (what you can do now)
- **Deliverables**
  - A short write-up in `python_expert_learning/SUMMARY.md` (append) with:
    - what you built
    - what you profiled
    - where you improved memory/time
    - what you want next (week 3 focus)
- **Final practice**
  - Re-solve your hardest problem from the last 10 days **from scratch** (no peeking).

---

## What “good expertise” looks like after 10 days
- You can **profile memory** and explain “why this line allocates”.
- You can choose between **generator vs list**, **chunking**, and **dtype tuning**.
- You can implement **threading vs multiprocessing vs asyncio** correctly for the workload.
- You can write small programs with **tests**, and iterate quickly without breaking behavior.

---

## Optional extension: Week 3 Integrations (recommended)

If you want to add real-world backend/data integrations (MySQL/Postgres/Redis/Kafka/PySpark), continue with Week 3:

- Start: `python_expert_learning/week3/START_HERE.md`
- Topics:
  - `python_expert_learning/week3/topics/01_sql_databases_mysql_postgres.md`
  - `python_expert_learning/week3/topics/02_redis_caching_patterns.md`
  - `python_expert_learning/week3/topics/03_kafka_basics_for_python.md`
  - `python_expert_learning/week3/topics/04_pyspark_fundamentals.md`
  - `python_expert_learning/week3/topics/05_mini_project_data_pipeline.md`


