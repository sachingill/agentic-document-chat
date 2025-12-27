"""
Week 3 - Exercise 4: PySpark word count (with pure Python fallback)

If pyspark is installed, this runs a tiny Spark DataFrame job.
Otherwise it runs a pure-Python version so the exercise still teaches the idea.

Run:
  python python_expert_learning/week3/exercises/04_pyspark_wordcount.py
"""

from __future__ import annotations

from collections import Counter


TEXT = [
    "spark is fast",
    "spark is lazy",
    "python talks to spark",
    "kafka to spark to postgres",
]


def pure_python_wordcount(lines: list[str]) -> dict[str, int]:
    words = []
    for line in lines:
        words.extend(line.split())
    return dict(Counter(words))


def pyspark_wordcount(lines: list[str]) -> dict[str, int]:
    from pyspark.sql import SparkSession  # type: ignore
    from pyspark.sql import functions as F  # type: ignore

    spark = (
        SparkSession.builder.master("local[*]")
        .appName("week3-wordcount")
        .getOrCreate()
    )
    try:
        df = spark.createDataFrame([(x,) for x in lines], ["line"])
        # transformations (lazy)
        words = df.select(F.explode(F.split(F.col("line"), " ")).alias("word"))
        counts = words.groupBy("word").count()
        # action (executes)
        rows = counts.collect()
        return {r["word"]: int(r["count"]) for r in rows}
    finally:
        spark.stop()


def main() -> None:
    try:
        out = pyspark_wordcount(TEXT)
        print("PySpark:", out)
        print("\n✅ PySpark ran. Next steps:")
        print("- Add a filter for stopwords")
        print("- Add a join with a lookup table (small dimension data)")
        print("- Explain: which lines are actions vs transformations")
    except Exception:
        out = pure_python_wordcount(TEXT)
        print("Pure Python (fallback):", out)
        print("\n(Optional) Install pyspark to run the Spark version, then rerun this file.")


if __name__ == "__main__":
    main()


