# Agentic vs Structured RAG - Visual Comparison

## 🔄 Flow Comparison

### Structured RAG (Parent Directory)

```
┌─────────────────────────────────────────────────────────┐
│                    FIXED FLOW                            │
└─────────────────────────────────────────────────────────┘

User Query
    ↓
[decompose] ← Always breaks into sub-queries
    ↓
[multi_query_retrieve] ← Always retrieves for each sub-query
    ↓
[rerank] ← Always reranks
    ↓
[generate] ← Always generates
    ↓
END

Characteristics:
- ✅ Predictable (always same path)
- ✅ Fast (no extra LLM calls for decisions)
- ❌ Fixed (can't adapt to question type)
- ❌ No tool selection (always uses retrieve_tool)
- ❌ No refinement (single pass)
```

### Agentic RAG (This Directory)

```
┌─────────────────────────────────────────────────────────┐
│                  DYNAMIC FLOW                            │
└─────────────────────────────────────────────────────────┘

User Query
    ↓
┌─────────────────────────────────────┐
│  [tool_selection]                   │
│  LLM decides: Which tool?           │
│  - retrieve_tool?                   │
│  - keyword_search_tool?             │
│  - metadata_search_tool?            │
│  - summarize_tool?                  │
└───────────────┬─────────────────────┘
                ↓
┌─────────────────────────────────────┐
│  [tool_execution]                   │
│  Execute selected tool dynamically  │
└───────────────┬─────────────────────┘
                ↓
┌─────────────────────────────────────┐
│  [reasoning]                        │
│  LLM evaluates:                     │
│  - Have enough info?                │
│  - Answer complete?                 │
│  - Need more context?               │
└───────────────┬─────────────────────┘
                ↓
        [CONDITIONAL ROUTING]
                ↓
        ┌───────┴───────┐
        │               │
    continue/refine    end
        │               │
        ↓               ↓
  [tool_selection]  [generate]
        │               │
        └───────┬───────┘
                ↓
            [LOOP BACK]
                ↓
            END

Characteristics:
- ✅ Dynamic (adapts to question)
- ✅ Tool selection (LLM chooses)
- ✅ Iterative refinement (can loop)
- ✅ Reasoning (LLM evaluates)
- ⚠️ More LLM calls (cost)
- ⚠️ Slower (more steps)
```

---

## 🎯 Decision Points Comparison

### Structured RAG: No Decisions

```
Every query follows the same path:
decompose → retrieve → rerank → generate

No decisions made.
No tool selection.
No routing choices.
```

### Agentic RAG: Multiple Decisions

```
Decision 1: Which tool to use?
  - LLM analyzes question
  - Chooses: retrieve_tool, keyword_search_tool, etc.

Decision 2: Is answer complete?
  - LLM evaluates context
  - Decides: continue, refine, or end

Decision 3: Route to next step
  - Based on decision 2
  - Routes: tool_selection (loop) or generate (end)
```

---

## 📊 Code Comparison

### Structured: Fixed Edges

```python
# All edges are fixed - always same path
graph.add_edge("decompose", "multi_query_retrieve")
graph.add_edge("multi_query_retrieve", "rerank")
graph.add_edge("rerank", "generate")
graph.add_edge("generate", END)
```

### Agentic: Conditional Edges

```python
# Conditional routing - path changes based on decision
graph.add_conditional_edges(
    "reasoning",
    should_continue,  # Function that decides next node
    {
        "tool_selection": "tool_selection",  # Can loop back!
        "generate": "generate",
        "end": END
    }
)
```

---

## 🔍 Example: Same Question, Different Flows

### Question: "What is SIM provisioning?"

#### Structured RAG Flow:
```
1. decompose → ["SIM provisioning definition", "provisioning process"]
2. multi_query_retrieve → 10 docs (5 per sub-query)
3. rerank → Top 5 docs
4. generate → Answer
5. END

Total: 4 steps, always same
```

#### Agentic RAG Flow (Example):
```
1. tool_selection → LLM: "retrieve_tool" (semantic search)
2. tool_execution → Retrieved 5 docs
3. reasoning → LLM: "Have enough info" → end
4. generate → Answer
5. END

Total: 4 steps, but LLM made decisions
```

### Question: "Compare circuit breaker and load balancing"

#### Structured RAG Flow:
```
1. decompose → ["circuit breaker", "load balancing", "comparison"]
2. multi_query_retrieve → 15 docs (5 per sub-query)
3. rerank → Top 5 docs
4. generate → Answer (might miss some info)
5. END

Total: 4 steps, might not have all info
```

#### Agentic RAG Flow (Example):
```
1. tool_selection → LLM: "retrieve_tool" (circuit breaker)
2. tool_execution → 3 docs about circuit breaker
3. reasoning → LLM: "Need load balancing info too" → continue
4. [LOOP BACK]
5. tool_selection → LLM: "retrieve_tool" (load balancing)
6. tool_execution → 3 docs about load balancing
7. reasoning → LLM: "Have both, can compare" → end
8. generate → Comprehensive answer
9. END

Total: 8 steps, but gets all needed info
```

---

## 💡 Key Insights

### When Structured is Better:
- ✅ Simple, straightforward questions
- ✅ Need fast responses
- ✅ Cost is a concern
- ✅ Predictable behavior required

### When Agentic is Better:
- ✅ Complex, multi-part questions
- ✅ Need adaptive behavior
- ✅ Questions require multiple tools
- ✅ Quality over speed/cost

---

## 🎓 Summary

**Structured RAG** = Fixed pipeline, predictable, fast
**Agentic RAG** = Dynamic system, adaptive, can refine

Both have their place! Use structured for simple queries, agentic for complex ones.

