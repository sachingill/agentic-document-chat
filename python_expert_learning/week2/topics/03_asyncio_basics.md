# Asyncio basics (enough to build real tools)

## Mental model
- **async def** defines a coroutine.
- **await** yields control back to the event loop so other tasks can run.
- Asyncio is great for **many concurrent IO tasks** (HTTP, sockets).

## Key rules
- Use **asyncio.gather** to run many coroutines concurrently.
- Use a **Semaphore** to cap concurrency (avoid blowing up your machine / remote service).
- Always set **timeouts** around network IO.

## Minimal pattern

```python
import asyncio

async def work(i: int) -> int:
    await asyncio.sleep(0.1)  # pretend IO
    return i * 2

async def main() -> None:
    results = await asyncio.gather(*(work(i) for i in range(10)))
    print(results)

if __name__ == "__main__":
    asyncio.run(main())
```

## Exercise
Complete: `python_expert_learning/week2/exercises/02_asyncio_url_checker.py`


