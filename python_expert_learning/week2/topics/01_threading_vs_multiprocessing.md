# Threading vs Multiprocessing (Practical)

## What you’re deciding
- **Threading**: multiple threads inside one Python process.
- **Multiprocessing**: multiple OS processes (separate Python interpreters).

## The rule of thumb
- **IO-bound** (network, disk, waiting): prefer **threads** or **asyncio**.
- **CPU-bound** (pure compute): prefer **multiprocessing** (or native extensions that release the GIL).

## Why: the GIL (very short)
CPython has a **Global Interpreter Lock (GIL)**. Only **one thread** executes Python bytecode at a time.
- For **CPU-bound** Python code: threads often don’t speed up.
- For **IO-bound** work: threads help because the GIL is released while waiting on IO.

## What can go wrong
- **Threads**
  - shared memory → races, inconsistent state
  - need locks/queues for coordination
- **Processes**
  - higher overhead (startup + IPC)
  - data must be serialized to move between processes

## Practical patterns
- **ThreadPoolExecutor** for IO-bound fan-out (fetch many URLs, read many files).
- **ProcessPoolExecutor / multiprocessing.Pool** for CPU-bound map/reduce (hashing, parsing + heavy compute).
- Use **queues** to avoid shared-state bugs.

## Exercises
Complete: `python_expert_learning/week2/exercises/01_concurrency_basics.py`


