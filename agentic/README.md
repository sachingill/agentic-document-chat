# Agentic RAG System

## 🎯 What Makes This Agentic?

This is a **fully agentic** RAG system, different from the structured RAG in the parent directory.

### Key Differences

| Feature | Structured RAG | **Agentic RAG** |
|---------|---------------|-----------------|
| **Flow** | Fixed (always same path) | **Dynamic (LLM decides)** |
| **Tool Selection** | Hardcoded (always retrieve) | **LLM chooses tools** |
| **Routing** | Linear (fixed edges) | **Conditional (based on decisions)** |
| **Iteration** | Single pass | **Can loop back to refine** |
| **Decision Making** | None | **LLM reasons about next steps** |

---

## 🏗️ Architecture

### Agentic Flow

```
User Query
    ↓
Input Guardrail
    ↓
┌─────────────────────────────────────┐
│  TOOL SELECTION NODE (AGENTIC!)    │
│  LLM decides which tool to use     │
└───────────────┬─────────────────────┘
                ↓
┌─────────────────────────────────────┐
│  TOOL EXECUTION NODE                │
│  Execute selected tool dynamically  │
└───────────────┬─────────────────────┘
                ↓
┌─────────────────────────────────────┐
│  REASONING NODE (AGENTIC!)          │
│  LLM evaluates: continue/refine/end │
└───────────────┬─────────────────────┘
                ↓
        [CONDITIONAL ROUTING]
                ↓
        ┌───────┴───────┐
        │               │
    continue/refine    end
        │               │
        ↓               ↓
  tool_selection    generate
        │               │
        └───────┬───────┘
                ↓
            [LOOP BACK]
                ↓
        Output Guardrail
                ↓
        Final Response
```

---

## 🚀 How to Run

### 1. Setup

```bash
cd agentic

# Use same virtual environment as main project
source ../venv/bin/activate

# Environment variables are loaded from parent .env
```

### 2. Start Server

```bash
# From agentic directory
uvicorn app.main:app --reload --port 8001
```

**Note**: Using port 8001 to avoid conflict with main API (port 8000)

### 3. Test Agentic Agent

```bash
curl -X POST "http://localhost:8001/agentic/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How does circuit breaker protect A1?",
    "session_id": "agentic-test"
  }'
```

---

## 🔍 How It Works

### Step 1: Tool Selection (Agentic!)

The LLM analyzes the question and decides which tool to use:

```python
# LLM sees question and available tools
# Decides: "This needs semantic search" → retrieve_tool
# Or: "This needs exact keyword match" → keyword_search_tool
# Or: "This needs metadata filter" → metadata_search_tool
```

**Example**:
- Question: "What is SIM provisioning?" 
- LLM Decision: `retrieve_tool` (semantic search)

- Question: "Find documents with topic=circuit_breaker"
- LLM Decision: `metadata_search_tool` (metadata filter)

### Step 2: Tool Execution

Execute the tool the LLM selected (dynamic, not hardcoded).

### Step 3: Reasoning (Agentic!)

LLM evaluates if answer is complete:

```python
# LLM reasons:
# - "Have enough context?" → continue/end
# - "Answer complete?" → refine/end
# - "Need more info?" → continue
```

### Step 4: Conditional Routing

Route based on LLM's decision:
- `continue` → Loop back to tool_selection (get more info)
- `refine` → Loop back to tool_selection (improve answer)
- `end` → Generate final answer

### Step 5: Iterative Refinement

Can loop back multiple times to improve answer quality!

---

## 📊 Example Execution Flow

### Example 1: Simple Question (1 iteration)

```
Question: "What is SIM provisioning?"
    ↓
Tool Selection: retrieve_tool
    ↓
Tool Execution: Retrieved 5 docs
    ↓
Reasoning: "Have enough info" → end
    ↓
Generate Answer: "SIM provisioning is..."
    ↓
Done!
```

### Example 2: Complex Question (2-3 iterations)

```
Question: "Compare circuit breaker and load balancing"
    ↓
Tool Selection: retrieve_tool (circuit breaker)
    ↓
Tool Execution: Retrieved 3 docs about circuit breaker
    ↓
Reasoning: "Need more info about load balancing" → continue
    ↓
[LOOP BACK]
    ↓
Tool Selection: retrieve_tool (load balancing)
    ↓
Tool Execution: Retrieved 3 docs about load balancing
    ↓
Reasoning: "Have enough info" → end
    ↓
Generate Answer: "Circuit breaker... Load balancing..."
    ↓
Done!
```

---

## 🆚 Comparison: Structured vs Agentic

### Structured RAG (Parent Directory)

```python
# Always same flow
decompose → retrieve → rerank → generate → END
```

**Pros**:
- ✅ Predictable
- ✅ Fast
- ✅ Cost-effective

**Cons**:
- ❌ Fixed flow
- ❌ No tool selection
- ❌ No refinement

### Agentic RAG (This Directory)

```python
# Dynamic flow
tool_selection → tool_execution → reasoning → [conditional routing]
    ↑                                              ↓
    └─────────────── [can loop back] ─────────────┘
```

**Pros**:
- ✅ Dynamic tool selection
- ✅ Can refine iteratively
- ✅ Adapts to question type
- ✅ Handles complex queries

**Cons**:
- ❌ More LLM calls (cost)
- ❌ Slower (more steps)
- ❌ Less predictable

---

## 🔧 Configuration

Uses same `.env` file as main project:
- `OPENAI_API_KEY` - Required
- `LANGSMITH_API_KEY` - Optional
- `LANGSMITH_TRACING` - Optional

---

## 📝 API Endpoints

### POST `/agentic/chat`

Chat with agentic agent:

```bash
curl -X POST "http://localhost:8001/agentic/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Your question here",
    "session_id": "optional-session-id"
  }'
```

### POST `/agentic/ingest/json`

Ingest documents (uses same vector DB as main project):

```bash
curl -X POST "http://localhost:8001/agentic/ingest/json" \
  -H "Content-Type: application/json" \
  -d '{
    "texts": ["Document 1", "Document 2"]
  }'
```

---

## 🎓 Key Concepts

### 1. Tool Selection
- **What**: LLM decides which tool to use
- **Why**: Different questions need different tools
- **Example**: Semantic search vs keyword search vs metadata filter

### 2. Conditional Routing
- **What**: Path changes based on LLM's decision
- **Why**: Enables dynamic flow
- **Example**: Continue if need more info, end if have enough

### 3. Iterative Refinement
- **What**: Can loop back to improve answer
- **Why**: Complex questions need multiple information gathering steps
- **Example**: First get info about A, then get info about B, then compare

### 4. Reasoning
- **What**: LLM evaluates if answer is complete
- **Why**: Knows when to stop or continue
- **Example**: "Have enough context? Yes → end, No → continue"

---

## 🧪 Testing

### Test Agentic Flow

```bash
# Start server
uvicorn app.main:app --reload --port 8001

# Test simple question
curl -X POST "http://localhost:8001/agentic/chat" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is SIM provisioning?"}'

# Test complex question (should trigger multiple iterations)
curl -X POST "http://localhost:8001/agentic/chat" \
  -H "Content-Type: application/json" \
  -d '{"question": "Compare circuit breaker and load balancing"}'
```

---

## 📈 When to Use Agentic vs Structured

### Use Structured RAG when:
- ✅ Simple, straightforward questions
- ✅ Need fast responses
- ✅ Cost is a concern
- ✅ Predictable behavior required

### Use Agentic RAG when:
- ✅ Complex, multi-part questions
- ✅ Need adaptive behavior
- ✅ Questions require multiple tools
- ✅ Quality over speed/cost

---

## 🔗 Related

- **Main Project**: `../` (Structured RAG)
- **Shared Vector DB**: `../ragdb/`
- **Shared Tools**: Same tools, used dynamically

---

**This is a fully agentic system!** 🚀

