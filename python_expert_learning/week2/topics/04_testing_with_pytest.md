# Testing with pytest (practical)

## Why pytest
- fast feedback
- clean assertions
- fixtures for setup

## Run tests
From repo root:

```bash
pytest -q
```

If you want to run only your learning tests:

```bash
pytest -q python_expert_learning
```

## Minimal test file
Create a file named `test_*.py` and write plain asserts:

```python
def add(a: int, b: int) -> int:
    return a + b

def test_add():
    assert add(1, 2) == 3
```

## What to test in this curriculum
- pure functions (easy)
- concurrency functions (harder): focus on **deterministic boundaries**
  - parsing
  - batching
  - retry logic
  - timeout behavior (with small timeouts)


