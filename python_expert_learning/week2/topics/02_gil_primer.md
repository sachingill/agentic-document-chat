# The GIL (Global Interpreter Lock) — what you need in practice

## The one-sentence definition
In **CPython**, the **GIL** is a lock that ensures **only one thread executes Python bytecode at a time**.

## What the GIL does *not* mean
- Threads are still useful for **IO** (waiting on sockets/files/timeouts).
- C extensions (e.g., parts of NumPy) may **release the GIL** during heavy work.

## Decision table
| Workload | Examples | Best tool |
|---|---|---|
| IO-bound | HTTP calls, DB queries, reading files | threads or asyncio |
| CPU-bound (pure Python) | parsing + heavy loops, compression, crypto in Python | multiprocessing |
| CPU-bound (native) | vectorized NumPy, some image ops | depends (may scale in threads) |

## Common trap
“I used threads and it didn’t speed up my CPU code.”
- That’s often expected in CPython.
- Use processes, or move hot loops into native code.

## Exercise
Run: `python python_expert_learning/week2/exercises/01_concurrency_basics.py`


