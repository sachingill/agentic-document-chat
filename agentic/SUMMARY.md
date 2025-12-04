# Agentic RAG System - Summary

## ✅ What We Built

A **fully agentic RAG system** in the `agentic/` subfolder that demonstrates true agentic behavior with:
- LLM-based tool selection
- Conditional routing
- Iterative refinement
- Dynamic decision-making

---

## 📁 Project Structure

```
api/
├── app/                    # Structured RAG (fixed pipeline)
│   └── agents/
│       └── doc_agent.py   # Fixed flow: decompose → retrieve → rerank → generate
│
└── agentic/                # Agentic RAG (dynamic flow)
    └── app/
        └── agents/
            └── agentic_agent.py  # Dynamic flow: tool_selection → reasoning → [can loop]
```

---

## 🔑 Key Differences

| Feature | Structured RAG | Agentic RAG |
|---------|---------------|-------------|
| **Tool Selection** | Hardcoded (always retrieve) | ✅ LLM decides |
| **Routing** | Fixed edges | ✅ Conditional edges |
| **Iteration** | Single pass | ✅ Can loop back |
| **Reasoning** | None | ✅ LLM reasons |
| **Flow** | Deterministic | ✅ Dynamic |

---

## 🚀 Quick Start

### Run Structured RAG:
```bash
uvicorn app.main:app --reload --port 8000
```

### Run Agentic RAG:
```bash
cd agentic
uvicorn app.main:app --reload --port 8001
```

---

## 📚 Documentation

- `README.md` - Complete guide
- `STEP_BY_STEP_BUILD.md` - Detailed build explanation
- `COMPLETE_EXPLANATION.md` - Full interactive explanation
- `AGENTIC_VS_STRUCTURED.md` - Visual comparison
- `QUICK_START.md` - Quick start guide

---

**Both systems are ready to use!** 🎉

