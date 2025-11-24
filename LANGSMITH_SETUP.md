# LangSmith Observability Setup Guide

This guide explains how LangSmith observability is configured in this project, step by step.

## What is LangSmith?

**LangSmith** is LangChain's observability platform that provides:
- **Tracing**: Track all LLM calls, tool invocations, and agent steps in real-time
- **Monitoring**: Performance metrics, latency, token usage, costs
- **Debugging**: Inspect prompts, responses, and intermediate states
- **Evaluation**: Test and compare different prompts/models
- **Analytics**: Understand usage patterns and optimize performance

---

## Step-by-Step Configuration

### Step 1: Install LangSmith Package

**File**: `requirements.txt`

```python
langsmith>=0.1.0
```

**Explanation**: 
- LangSmith is installed as a separate package
- It integrates automatically with LangChain/LangGraph components
- The `>=0.1.0` ensures we get the latest features

**Action**: Run `pip install -r requirements.txt`

---

### Step 2: Create Configuration Module

**File**: `app/config.py`

**Purpose**: Centralized configuration for LangSmith settings

**Key Components**:

1. **API Key**: Your LangSmith API key (get from https://smith.langchain.com/settings)
   ```python
   API_KEY = os.getenv("LANGSMITH_API_KEY", "")
   ```

2. **Endpoint**: LangSmith API endpoint (default is cloud)
   ```python
   ENDPOINT = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
   ```

3. **Tracing Toggle**: Enable/disable tracing
   ```python
   TRACING = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
   ```

4. **Project Name**: Organize traces in LangSmith dashboard
   ```python
   PROJECT_NAME = os.getenv("LANGSMITH_PROJECT", "rag-api")
   ```

5. **Tags**: Filter and organize traces
   ```python
   TAGS = os.getenv("LANGSMITH_TAGS", "production,rag").split(",")
   ```

**Why This Design**:
- Environment-based configuration (easy to switch between dev/prod)
- Automatic setup when module is imported
- Clear status messages on startup

---

### Step 3: Set Environment Variables

**File**: `.env` (create if it doesn't exist)

```bash
# LangSmith Configuration
LANGSMITH_API_KEY=your-api-key-here
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=rag-api
LANGSMITH_TAGS=production,rag,api
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
```

**How to Get API Key**:
1. Go to https://smith.langchain.com
2. Sign up or log in
3. Navigate to Settings → API Keys
4. Create a new API key
5. Copy it to your `.env` file

**Explanation**:
- `LANGSMITH_API_KEY`: Authenticates your application with LangSmith
- `LANGSMITH_TRACING=true`: Enables automatic tracing
- `LANGSMITH_PROJECT`: Groups all traces under this project name
- `LANGSMITH_TAGS`: Adds metadata tags for filtering in dashboard

---

### Step 4: Initialize Tracing in Main App

**File**: `app/main.py`

**Change**:
```python
# Import LangSmith config early to set up tracing
# This must be imported BEFORE any LangChain/LangGraph imports
from app.config import LangSmithConfig
```

**Why Early Import**:
- LangSmith needs to set environment variables **before** LangChain components are imported
- LangChain reads these environment variables at import time
- Order matters: Config → LangChain imports → FastAPI app

**What Happens**:
1. `LangSmithConfig.setup_environment()` is called automatically
2. Sets `LANGCHAIN_TRACING_V2=true` in environment
3. Sets `LANGCHAIN_API_KEY` from your config
4. Sets `LANGCHAIN_PROJECT` for organization
5. Prints status message: ✅ enabled or ⚠️ disabled

---

### Step 5: Add Explicit Tracing Decorators

**Purpose**: Add `@traceable` decorators to key functions for better observability

#### A. Document Agent (`app/agents/doc_agent.py`)

```python
from langsmith import traceable

@traceable(name="retrieve_node", run_type="tool")
async def retrieve_node(state: AgentState) -> AgentState:
    # Vector search and reranking
    ...

@traceable(name="generate_node", run_type="llm")
def generate_node(state: AgentState) -> AgentState:
    # LLM answer generation
    ...

@traceable(name="run_document_agent", run_type="chain")
async def run_document_agent(session_id: str, question: str):
    # Full RAG pipeline
    ...
```

**Explanation**:
- `@traceable`: Decorator that automatically logs function calls to LangSmith
- `name`: Human-readable name in LangSmith dashboard
- `run_type`: Categorizes the trace (tool, llm, chain, retriever, guardrail)

**Benefits**:
- See each step of RAG pipeline separately
- Track performance of each component
- Debug issues at granular level

#### B. Reranker (`app/agents/reranker.py`)

```python
@traceable(name="rerank", run_type="chain")
async def rerank(question: str, docs: List[str], top_k: int = 3):
    # Document reranking logic
    ...
```

**Why**: Reranking is a critical step - track its performance and scores

#### C. Tools (`app/agents/tools.py`)

```python
@traceable(name="retrieve_tool", run_type="retriever")
def retrieve_tool(query: str, k: int = 10):
    # Vector database retrieval
    ...
```

**Why**: Track retrieval performance and document counts

#### D. Guardrails (`app/agents/guardrails.py`)

```python
@traceable(name="check_input_safety", run_type="guardrail")
def check_input_safety(user_message: str) -> GuardrailResult:
    # Input safety checks
    ...

@traceable(name="check_output_safety", run_type="guardrail")
def check_output_safety(answer: str) -> GuardrailResult:
    # Output safety checks
    ...
```

**Why**: Monitor safety checks and blocked requests

---

### Step 6: Automatic Tracing (Already Works!)

**What's Automatically Traced** (no code changes needed):

1. **All ChatOpenAI calls**:
   - `llm.invoke()` in `doc_agent.py`
   - `rerank_llm.ainvoke()` in `reranker.py`
   - `_guard_llm.invoke()` in `guardrails.py`
   - `llm.invoke()` in `tools.py`

2. **LangGraph Agent Execution**:
   - Graph state transitions
   - Node executions
   - Edge traversals

3. **Vector Store Operations**:
   - ChromaDB queries
   - Document retrievals

**How It Works**:
- LangChain components automatically detect `LANGCHAIN_TRACING_V2=true`
- They send traces to LangSmith API
- No additional code needed!

---

## What You'll See in LangSmith Dashboard

### 1. **Traces View**
- Every API request creates a trace
- See the full RAG pipeline execution
- Timeline of all operations

### 2. **Metrics**
- **Latency**: How long each step takes
- **Token Usage**: Input/output tokens per call
- **Costs**: Estimated costs per request
- **Success Rate**: Failed vs successful requests

### 3. **Debugging**
- **Prompts**: See exact prompts sent to LLMs
- **Responses**: See LLM outputs
- **Intermediate States**: Vector search results, reranking scores
- **Errors**: Stack traces and error messages

### 4. **Filtering**
- By project name
- By tags (production, rag, api)
- By session ID
- By date range

---

## Testing the Setup

### 1. Verify Configuration

```bash
# Check if LangSmith is enabled
python -c "from app.config import LangSmithConfig; print(LangSmithConfig.is_enabled())"
```

Should print: `True` (if API key is set and tracing is enabled)

### 2. Make a Test Request

```bash
curl -X POST http://127.0.0.1:8000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-langsmith",
    "question": "What is SIM provisioning?",
    "reset_session": true
  }'
```

### 3. Check LangSmith Dashboard

1. Go to https://smith.langchain.com
2. Navigate to "Traces" section
3. You should see your request appear within seconds
4. Click on a trace to see detailed execution

---

## Troubleshooting

### Issue: Traces Not Appearing

**Check**:
1. ✅ `LANGSMITH_API_KEY` is set correctly
2. ✅ `LANGSMITH_TRACING=true` in `.env`
3. ✅ API key is valid (check at https://smith.langchain.com/settings)
4. ✅ Network connectivity (no firewall blocking)

**Debug**:
```python
from app.config import LangSmithConfig
print(f"Enabled: {LangSmithConfig.is_enabled()}")
print(f"API Key: {LangSmithConfig.API_KEY[:10]}...")  # First 10 chars
print(f"Project: {LangSmithConfig.PROJECT_NAME}")
```

### Issue: Too Many Traces

**Solution**: Disable tracing in development
```bash
LANGSMITH_TRACING=false
```

### Issue: Want Different Projects for Dev/Prod

**Solution**: Use different `.env` files
```bash
# .env.development
LANGSMITH_PROJECT=rag-api-dev

# .env.production
LANGSMITH_PROJECT=rag-api-prod
```

---

## Best Practices

1. **Use Descriptive Project Names**: `rag-api-prod`, `rag-api-staging`
2. **Add Meaningful Tags**: `production`, `staging`, `experiment-v2`
3. **Monitor Costs**: Check token usage regularly
4. **Set Up Alerts**: Configure alerts for high latency or errors
5. **Review Traces**: Periodically review traces to optimize prompts

---

## Summary

✅ **Step 1**: Install `langsmith` package  
✅ **Step 2**: Create `app/config.py` with configuration  
✅ **Step 3**: Set environment variables in `.env`  
✅ **Step 4**: Import config early in `app/main.py`  
✅ **Step 5**: Add `@traceable` decorators to key functions  
✅ **Step 6**: Automatic tracing works for all LangChain components  

**Result**: Full observability of your RAG pipeline in LangSmith dashboard!

