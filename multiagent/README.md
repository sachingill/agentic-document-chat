# 🤖 Multi-Agent RAG System

## Overview

This directory contains the multi-agent RAG system implementation using LangGraph. The system extends our existing Structured and Agentic RAG implementations with collaborative agent workflows.

## 📚 Documentation

- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - System architecture and design
- **[SPECIFICATIONS.md](./SPECIFICATIONS.md)** - Detailed specifications for agents, workflows, and APIs
- **[WORKFLOW_DIAGRAMS.md](./WORKFLOW_DIAGRAMS.md)** - Visual workflow diagrams

## 🎯 Quick Start

### Prerequisites

- Python 3.8+
- LangGraph
- LangChain
- OpenAI API key

### Installation

```bash
# Install dependencies (from project root)
pip install -r requirements.txt
```

### Usage (Python)

```python
import asyncio
from multiagent.app.agents.sequential_agent import run_sequential_agent

async def main():
    result = await run_sequential_agent(
        question="What is a circuit breaker?",
        session_id="session_123",
    )
    print(result["answer"])

asyncio.run(main())
```

### Usage (HTTP)

The multi-agent router exposes these endpoints:

- `POST /multiagent/sequential/chat`
- `POST /multiagent/parallel/chat`
- `POST /multiagent/supervisor/chat`
- `POST /multiagent/chat` (**auto-select**)

Example (auto-select):

```bash
curl -X POST "http://localhost:8000/multiagent/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Explain how to implement circuit breaker in microservices with code examples",
    "session_id": "session_123",
    "auto_select_pattern": true
  }'
```

Budget-aware auto-select (soft constraints using relative estimates):

```bash
curl -X POST "http://localhost:8000/multiagent/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Explain how to implement circuit breaker in microservices with code examples",
    "session_id": "session_123",
    "auto_select_pattern": true,
    "max_relative_cost": 1.2,
    "max_relative_latency": 1.2
  }'
```

To force a specific pattern:

```bash
curl -X POST "http://localhost:8000/multiagent/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is a circuit breaker?",
    "session_id": "session_123",
    "auto_select_pattern": false,
    "pattern": "sequential"
  }'
```

## 🏗️ Architecture

The system implements three main patterns:

1. **Sequential Pipeline**: Research → Analysis → Synthesis
2. **Parallel Competitive**: Multiple agents compete, best answer wins
3. **Supervisor-Worker**: Supervisor delegates to specialized workers

## 📁 Directory Structure

```
multiagent/
├── app/
│   ├── agents/
│   │   ├── sequential_agent.py      # Sequential pattern
│   │   ├── parallel_agent.py        # Parallel pattern
│   │   ├── supervisor_agent.py      # Supervisor pattern
│   │   ├── research_agent.py        # Research agent
│   │   ├── analysis_agent.py        # Analysis agent
│   │   ├── synthesis_agent.py       # Synthesis agent
│   │   ├── evaluator_agent.py       # Evaluator agent
│   │   └── workers.py               # Worker agents
│   ├── routers/
│   │   └── multiagent.py            # FastAPI router
│   └── models/
│       └── state.py                 # State definitions
├── ARCHITECTURE.md
├── SPECIFICATIONS.md
├── WORKFLOW_DIAGRAMS.md
└── README.md
```

## 🚀 Implementation Status

- [x] Phase 1: Foundation
- [x] Phase 2: Sequential Pattern
- [x] Phase 3: Parallel Pattern
- [x] Phase 4: Supervisor-Worker Pattern
- [x] Phase 5: Integration & Polish (initial)

### Auto-select Pattern

`POST /multiagent/chat` supports auto-selecting an execution pattern.

- Default selection is **heuristic**
- Optional LLM selection: set `MULTIAGENT_PATTERN_SELECTOR_MODE=llm`
- The response includes selection details in `metadata`:
  - `pattern_selected`
  - `pattern_selection_mode`
  - `pattern_selection_reasoning`
  - `pattern_selection_estimates`

### Learning-based tuning (logging)

You can optionally log selection events (JSONL) to tune prompts/thresholds from real traffic:

- Enable logging: `MULTIAGENT_SELECTION_LOG_ENABLED=true`
- Optional path: `MULTIAGENT_SELECTION_LOG_PATH=/path/to/multiagent_selection_events.jsonl`

## 📝 Next Steps

1. Mature inference: improve pattern selection + worker planning + answer verification
2. Add stronger evaluation/grounding signals (citations, context checks, uncertainty)
3. Add performance controls (timeouts, budgets, caching)

## 🔗 Related

- [Structured RAG](../app/agents/doc_agent.py)
- [Agentic RAG](../agentic/app/agents/agentic_agent.py)
- [Tools](../app/agents/tools.py)

