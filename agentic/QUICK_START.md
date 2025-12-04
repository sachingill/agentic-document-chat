# Agentic RAG - Quick Start Guide

## 🚀 Quick Setup

### 1. Navigate to Agentic Directory

```bash
cd agentic
```

### 2. Use Same Virtual Environment

```bash
# From agentic directory
source ../venv/bin/activate
```

### 3. Start Agentic Server

```bash
# Uses port 8001 to avoid conflict with main API (port 8000)
uvicorn app.main:app --reload --port 8001
```

### 4. Test Agentic Agent

```bash
curl -X POST "http://localhost:8001/agentic/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How does circuit breaker protect A1?",
    "session_id": "agentic-test"
  }'
```

---

## 🔍 What Makes It Agentic?

### 1. LLM Chooses Tools
- Analyzes question
- Selects appropriate tool
- Not hardcoded

### 2. Dynamic Routing
- Path changes based on LLM's decision
- Can loop back to refine
- Not fixed

### 3. Iterative Refinement
- Can gather info in multiple steps
- Can improve answer quality
- Handles complex queries

---

## 📊 Example Execution

Watch the logs to see agentic decisions:

```
🤖 Agent selected tool: retrieve_tool (iteration 1)
🔧 Executing tool: retrieve_tool
🧠 Agent reasoning: Need more information → continue
🔄 Routing: continue → tool_selection (get more info)
🤖 Agent selected tool: keyword_search_tool (iteration 2)
🔧 Executing tool: keyword_search_tool
🧠 Agent reasoning: Have enough information → end
🔄 Routing: end → generate (finalize answer)
✅ Answer generated: 148 chars
```

---

## 🆚 Compare with Structured RAG

### Structured (Port 8000):
```bash
curl -X POST "http://localhost:8000/agent/chat" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is SIM provisioning?"}'
```

### Agentic (Port 8001):
```bash
curl -X POST "http://localhost:8001/agentic/chat" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is SIM provisioning?"}'
```

Compare the responses and execution flow!

---

## 📝 Key Files

- `app/agents/agentic_agent.py` - Main agentic agent
- `app/routers/agentic_agent.py` - API router
- `app/main.py` - FastAPI application
- `README.md` - Full documentation
- `STEP_BY_STEP_BUILD.md` - Detailed build explanation

---

**Ready to use!** 🎉

