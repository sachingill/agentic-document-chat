# Current RAG Flow - Complete Overview

## 🏗️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Endpoint                              │
│              POST /agent/chat                                    │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 1: INPUT GUARDRAIL                                        │
│  ────────────────────────                                       │
│  • check_input_safety()                                         │
│  • Uses: gpt-4o-mini (temperature=0)                            │
│  • Checks: Prompt injection, harmful content, bypass attempts   │
│  • Result: ALLOW or BLOCK                                        │
└───────────────────────────┬─────────────────────────────────────┘
                            │ (if ALLOW)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 2: DOCUMENT AGENT (LangGraph)                            │
│  ───────────────────────────────────                           │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Node 1: RETRIEVE NODE (async)                            │ │
│  │  ──────────────────────────────                          │ │
│  │                                                           │ │
│  │  A) Vector Search                                        │ │
│  │     • retrieve_tool(query, k=10)                         │ │
│  │     • Uses: ChromaDB vector store                        │ │
│  │     • Embedding: sentence-transformers/all-MiniLM-L6-v2  │ │
│  │     • Retrieves: Top 10 documents (increased for rerank) │ │
│  │                                                           │ │
│  │  B) Reranking (if docs found)                            │ │
│  │     • rerank(question, docs, top_k=3)                    │ │
│  │     • Uses: gpt-4o-mini (temperature=0)                  │ │
│  │     • Process:                                            │ │
│  │       1. Score each doc chunk (0-1 relevance)            │ │
│  │       2. Parallel async scoring (asyncio.gather)        │ │
│  │       3. Sort by score (descending)                      │ │
│  │       4. Return top 3 chunks                             │ │
│  │                                                           │ │
│  │  Output: state["context"] = [top 3 ranked chunks]        │ │
│  └───────────────────────────┬───────────────────────────────┘ │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Node 2: GENERATE NODE                                     │ │
│  │  ────────────────────────                                 │ │
│  │                                                           │ │
│  │  • Gets: context (top 3 chunks) + conversation history    │ │
│  │  • Uses: gpt-4o (temperature=0.1)                         │ │
│  │  • Prompt:                                                │ │
│  │    - Context: Top 3 reranked documents                    │ │
│  │    - History: Previous conversation turns (max 6)         │ │
│  │    - Question: User's question                             │ │
│  │    - Rules: Strict RAG, respond "I don't know" if no     │ │
│  │             answer in context                              │ │
│  │  • Saves: Conversation to Memory                          │ │
│  │  • Output: state["answer"] = LLM response                 │ │
│  └───────────────────────────┬───────────────────────────────┘ │
│                              │                                   │
└──────────────────────────────┼───────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 3: OUTPUT GUARDRAIL                                      │
│  ────────────────────────                                       │
│  • check_output_safety(answer)                                 │
│  • Uses: gpt-4o-mini (temperature=0)                           │
│  • Checks: Unsafe/harmful content in response                  │
│  • Result: ALLOW (return as-is) or REDACT (sanitize)          │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Final Response                                │
│  {                                                              │
│    "answer": "...",                                            │
│    "guardrail": {                                              │
│      "stage": "none" | "output",                               │
│      "blocked": false | true,                                  │
│      "reason": null | "..."                                    │
│    }                                                            │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 Complete Flow Breakdown

### **Entry Point: `/agent/chat` API**

**File**: `app/routers/agent.py`

**Input**:
```json
{
  "session_id": "user-session-123",
  "question": "How does circuit breaker protect A1?",
  "reset_session": false
}
```

---

### **Step 1: Input Guardrail** 🔒

**File**: `app/agents/guardrails.py`  
**Function**: `check_input_safety()`

**What it does**:
- Uses `gpt-4o-mini` (temperature=0) as a security classifier
- Checks for:
  - Prompt injection attempts
  - System instruction bypasses
  - Harmful/illegal content requests
  - Guardrail override attempts

**Decision**:
- `ALLOW` → Continue to RAG agent
- `BLOCK` → Return error, stop processing

**Traced**: ✅ Yes (`@traceable`)

---

### **Step 2: Document Agent (LangGraph)** 🤖

**File**: `app/agents/doc_agent.py`  
**Function**: `run_document_agent()`

**Graph Structure**:
```
START → retrieve_node → generate_node → END
```

#### **Node 1: Retrieve Node** (`retrieve_node`)

**A. Vector Search** (`retrieve_tool`)
- **File**: `app/agents/tools.py`
- **Vector DB**: ChromaDB (persisted in `./ragdb`)
- **Embeddings**: HuggingFace `sentence-transformers/all-MiniLM-L6-v2`
- **Retrieval**: Top **10 documents** (k=10, increased for reranking)
- **Method**: Cosine similarity search on embeddings

**B. Reranking** (`rerank`)
- **File**: `app/agents/reranker.py`
- **Model**: `gpt-4o-mini` (temperature=0)
- **Process**:
  1. For each of 10 retrieved docs:
     - Send to LLM: "Score relevance 0-1 for this question"
     - Get numeric score
     - Clamp to [0, 1] range
  2. **Parallel Processing**: All 10 docs scored simultaneously (`asyncio.gather`)
  3. Sort by score (highest first)
  4. Return **top 3** chunks

**Why Two-Stage Retrieval?**
- **Vector search**: Fast, semantic similarity (catches related concepts)
- **Reranking**: Precise relevance scoring (LLM understands context better)
- **Result**: Best of both worlds - fast + accurate

**Output**: `state["context"] = [top 3 ranked document chunks]`

**Traced**: ✅ Yes (both `retrieve_tool` and `rerank` have `@traceable`)

---

#### **Node 2: Generate Node** (`generate_node`)

**What it does**:
1. **Gets Context**:
   - Top 3 reranked documents (from retrieve_node)
   - Conversation history (from Memory, max 6 turns)

2. **Builds Prompt**:
   ```
   You are a strict RAG assistant.
   Use ONLY the provided context to answer.
   
   Context: [top 3 chunks]
   History: [previous conversation]
   Question: [user question]
   
   RULES:
   - If answer not in context, respond "I don't know based on the documents."
   ```

3. **Calls LLM**:
   - Model: `gpt-4o` (temperature=0.1)
   - Low temperature = consistent, factual responses

4. **Saves to Memory**:
   - Stores (question, answer) pair for conversation history

**Output**: `state["answer"] = LLM response`

**Traced**: ✅ Yes (`@traceable`)

---

### **Step 3: Output Guardrail** 🔒

**File**: `app/agents/guardrails.py`  
**Function**: `check_output_safety()`

**What it does**:
- Uses `gpt-4o-mini` (temperature=0) as safety classifier
- Checks if answer contains:
  - Unsafe/harmful content
  - Disallowed information
  - Inappropriate responses

**Decision**:
- `ALLOW` → Return answer as-is
- `REDACT` → Replace with safe message: "I'm not able to answer that safely..."

**Traced**: ✅ Yes (`@traceable`)

---

## 🔧 Key Components

### **1. Vector Database**
- **Type**: ChromaDB
- **Location**: `./ragdb/` (persisted locally)
- **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2`
- **Chunk Size**: 800 characters, 200 overlap

### **2. LLM Models Used**

| Component | Model | Temperature | Purpose |
|-----------|-------|-------------|---------|
| Main Answer | gpt-4o | 0.1 | Generate final answer |
| Reranker | gpt-4o-mini | 0 | Score document relevance |
| Guardrails | gpt-4o-mini | 0 | Safety classification |
| Tools | gpt-4o-mini | 0.1 | Summarization (if used) |

### **3. Memory System**
- **Type**: In-memory session-based
- **Storage**: `{session_id: [(user_msg, assistant_msg), ...]}`
- **History**: Last 6 turns per session
- **File**: `app/models/memory.py`

### **4. Observability**
- **LangSmith**: All components traced
- **Logging**: Structured logging at each step
- **Metrics**: Latency, tokens, costs tracked

---

## 🔄 Complete Request Flow

```
1. User sends: POST /agent/chat
   ↓
2. Input Guardrail checks safety
   ↓ (if ALLOW)
3. Document Agent starts:
   ├─→ Vector Search (top 10)
   ├─→ Rerank (top 3, parallel scoring)
   └─→ Generate answer (gpt-4o)
   ↓
4. Output Guardrail checks safety
   ↓
5. Return response with guardrail status
```

---

## 📊 Performance Characteristics

### **Retrieval**
- **Vector Search**: ~50-100ms (depends on DB size)
- **Reranking**: ~500-2000ms (10 parallel LLM calls)
- **Total Retrieval**: ~600-2100ms

### **Generation**
- **LLM Call**: ~1000-3000ms (gpt-4o)
- **Total Generation**: ~1000-3000ms

### **Total Pipeline**
- **Best Case**: ~1.6 seconds
- **Average**: ~3-4 seconds
- **Worst Case**: ~5-6 seconds

---

## 🎯 Key Features

✅ **Two-Stage Retrieval**: Vector search + LLM reranking  
✅ **Parallel Reranking**: All docs scored simultaneously  
✅ **Conversation Memory**: Session-based history  
✅ **Input/Output Guardrails**: Safety at both ends  
✅ **Strict RAG**: Only answers from context  
✅ **LangSmith Tracing**: Full observability  
✅ **Error Handling**: Graceful degradation  
✅ **Async Support**: Non-blocking operations  

---

## 🔍 What Makes This RAG Flow Effective

1. **Two-Stage Retrieval**:
   - Vector search finds semantically similar docs (fast)
   - LLM reranking scores true relevance (accurate)
   - Result: Best of both approaches

2. **Parallel Processing**:
   - Reranking scores all docs simultaneously
   - Reduces latency significantly

3. **Strict RAG Prompting**:
   - Forces LLM to only use provided context
   - Prevents hallucination
   - Returns "I don't know" when context insufficient

4. **Safety Layers**:
   - Input guardrail: Prevents malicious queries
   - Output guardrail: Prevents unsafe responses
   - Defense in depth

5. **Observability**:
   - Every step traced in LangSmith
   - Easy to debug and optimize
   - Performance metrics available

---

## 📝 Files Involved

- `app/routers/agent.py` - API endpoint
- `app/agents/doc_agent.py` - LangGraph agent
- `app/agents/reranker.py` - Document reranking
- `app/agents/tools.py` - Retrieval tools
- `app/agents/guardrails.py` - Safety checks
- `app/models/embeddings.py` - Vector DB setup
- `app/models/memory.py` - Conversation history
- `app/config.py` - LangSmith configuration

---

This is your complete RAG pipeline! 🚀

