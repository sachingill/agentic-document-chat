"""
Week 3 - Exercise 1: SQL Foundations (sqlite3 first)

This exercise teaches production SQL patterns using built-in sqlite3,
so it runs anywhere. Then it shows how you'd swap to PostgreSQL/MySQL.

Run:
  python python_expert_learning/week3/exercises/01_sql_foundations_sqlite_first.py
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional


DB_PATH = Path(__file__).with_name("exercise_week3_sqlite.db")


@dataclass(frozen=True)
class User:
    id: int
    email: str
    name: str


def connect_sqlite(db_path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
    conn.commit()


def upsert_user(conn: sqlite3.Connection, *, email: str, name: str) -> None:
    """
    TODO (you): ensure this is safe (no SQL injection) and atomic.

    Hint: parameterized query + transaction.
    """
    with conn:
        conn.execute(
            """
            INSERT INTO users(email, name)
            VALUES(?, ?)
            ON CONFLICT(email) DO UPDATE SET name=excluded.name
            """,
            (email, name),
        )


def get_user_by_email(conn: sqlite3.Connection, *, email: str) -> Optional[User]:
    row = conn.execute(
        "SELECT id, email, name FROM users WHERE email = ?",
        (email,),
    ).fetchone()
    if row is None:
        return None
    return User(id=int(row["id"]), email=str(row["email"]), name=str(row["name"]))


def list_users(conn: sqlite3.Connection, *, limit: int = 10, offset: int = 0) -> list[User]:
    rows = conn.execute(
        "SELECT id, email, name FROM users ORDER BY id ASC LIMIT ? OFFSET ?",
        (int(limit), int(offset)),
    ).fetchall()
    return [User(id=int(r["id"]), email=str(r["email"]), name=str(r["name"])) for r in rows]


def main() -> None:
    conn = connect_sqlite()
    init_schema(conn)

    # Seed
    upsert_user(conn, email="ada@example.com", name="Ada")
    upsert_user(conn, email="grace@example.com", name="Grace")
    upsert_user(conn, email="ada@example.com", name="Ada Lovelace")  # update

    # Read
    ada = get_user_by_email(conn, email="ada@example.com")
    print("ada:", ada)

    # Pagination
    print("all:", list_users(conn, limit=10, offset=0))

    print("\n✅ Next steps (do these TODOs):")
    print("- Add a function: delete_user_by_email(conn, email)")
    print("- Add a function: count_users(conn)")
    print("- Explain: why parameterized queries prevent SQL injection")
    print("- Explain: what the `with conn:` block guarantees (commit/rollback)")
    print("\nOptional real DB:")
    print("- Postgres/MySQL: swap sqlite3 with a driver (psycopg / pymysql) OR use SQLAlchemy for pooling.")


if __name__ == "__main__":
    main()


