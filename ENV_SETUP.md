# How OPENAI_API_KEY is Read in This Project

## Current Flow

### 1. **Startup Sequence** (`app/main.py`)

```python
from dotenv import load_dotenv  # Line 1
import os                       # Line 2

load_dotenv()                   # Line 5 - Loads .env into os.environ

from fastapi import FastAPI     # Line 7
from app.routers import ...     # Line 8-9 - Imports routers
```

**Key Point:** `load_dotenv()` runs BEFORE any router imports, ensuring `.env` is loaded into `os.environ`.

### 2. **When Routers Import** (`app/routers/agent.py`)

```python
from app.agents.doc_agent import run_document_agent  # Imports doc_agent
```

### 3. **When doc_agent is Imported** (`app/agents/doc_agent.py`)

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o", temperature=0.1)  # Line 18 - Module-level instantiation
```

**At this point:** `ChatOpenAI` is created, but it doesn't read the API key yet.

### 4. **How ChatOpenAI Reads the Key**

`ChatOpenAI` reads `OPENAI_API_KEY` from `os.environ` **lazily** when:
- It makes its first API call (e.g., `llm.invoke()`)
- Not at instantiation time

**Internal mechanism:**
```python
# Inside ChatOpenAI (simplified)
api_key = os.getenv('OPENAI_API_KEY')  # Reads from environment
if not api_key:
    raise ValueError("OPENAI_API_KEY not set")
```

## Potential Issues & Solutions

### ✅ **Current Setup is CORRECT**

The import order ensures:
1. `load_dotenv()` runs first → loads `.env` into `os.environ`
2. Routers import → imports `doc_agent`
3. `doc_agent` creates `ChatOpenAI` → key is already in `os.environ`
4. When API call happens → `ChatOpenAI` reads from `os.environ`

### ⚠️ **Potential Issue: Direct Imports**

If someone imports `doc_agent` or `tools` directly (not through `main.py`):

```python
# ❌ BAD - Missing load_dotenv()
from app.agents.doc_agent import llm  # Will fail if .env not loaded
```

**Solution:** Always ensure `.env` is loaded before importing modules that use `ChatOpenAI`.

### ⚠️ **Issue: Missing API Key Error**

If `OPENAI_API_KEY` is not set, the error only appears when making an API call:

```python
llm.invoke("test")  # ❌ Error: "OPENAI_API_KEY not set"
```

**Better approach:** Validate at startup (see improvement below).

## Recommended Improvement

Add validation in `main.py`:

```python
from dotenv import load_dotenv
import os

load_dotenv()

# Validate API key is set
if not os.getenv('OPENAI_API_KEY'):
    raise ValueError(
        "OPENAI_API_KEY not found in environment. "
        "Please set it in .env file or environment variables."
    )

from fastapi import FastAPI
# ... rest of imports
```

## Summary

**How it works:**
1. `.env` file contains `OPENAI_API_KEY=your-key`
2. `load_dotenv()` loads it into `os.environ`
3. `ChatOpenAI` reads from `os.environ['OPENAI_API_KEY']` when needed
4. No explicit passing required - automatic!

**Current status:** ✅ Working correctly with proper import order.

