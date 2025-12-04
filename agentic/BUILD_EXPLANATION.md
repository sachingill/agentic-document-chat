# Building Agentic Flow - Detailed Step-by-Step Explanation

## 🎯 Goal

Transform the structured RAG pipeline into a **fully agentic system** where the LLM makes decisions about:
1. Which tools to use
2. When to continue/refine/end
3. How to route through the graph

---

## 📋 Step-by-Step Build Process

### **STEP 1: Enhanced Agent State** ✅

**What we did:**
```python
class AgenticState(TypedDict):
    session_id: str
    question: str
    context: List[str]
    answer: str
    tool_selection: Optional[str]      # NEW: Track which tool LLM selected
    tool_results: Optional[dict]       # NEW: Track tool execution results
    reasoning: Optional[str]           # NEW: Track LLM's reasoning
    iteration_count: int               # NEW: Prevent infinite loops
    should_continue: Optional[Literal["continue", "refine", "end"]]  # NEW: Routing decision
```

**Why:**
- Need to track agent's decisions
- Need to know which tool was used
- Need to track iterations to prevent loops
- Need routing decision for conditional edges

**Difference from Structured:**
- Structured: Only tracks `question`, `context`, `answer`
- Agentic: Tracks decisions, tool usage, reasoning, iterations

---

### **STEP 2: Tool Selection Node** ✅

**What we did:**
```python
def tool_selection_node(state: AgenticState) -> AgenticState:
    # LLM analyzes question and available tools
    # Decides which tool to use
    prompt = f"""
    Question: {question}
    Available tools: retrieve_tool, keyword_search_tool, ...
    Which tool should I use?
    """
    response = agent_llm.invoke(prompt)
    state["tool_selection"] = selected_tool
```

**Why:**
- **AGENTIC**: LLM makes the decision, not hardcoded
- Different questions need different tools
- Enables adaptive behavior

**Difference from Structured:**
- Structured: Always uses `retrieve_tool` (hardcoded)
- Agentic: LLM chooses from multiple tools

**Example:**
- Question: "What is SIM provisioning?" → LLM chooses `retrieve_tool`
- Question: "Find docs with topic=circuit_breaker" → LLM chooses `metadata_search_tool`
- Question: "Search for 'retry mechanism'" → LLM chooses `keyword_search_tool`

---

### **STEP 3: Tool Execution Node** ✅

**What we did:**
```python
def tool_execution_node(state: AgenticState) -> AgenticState:
    tool_name = state["tool_selection"]  # Get LLM's choice
    
    # Dynamically execute the selected tool
    if tool_name == "retrieve_tool":
        result = retrieve_tool(question)
    elif tool_name == "keyword_search_tool":
        result = keyword_search_tool(keyword)
    # ... etc
```

**Why:**
- Execute whatever tool the LLM selected
- Dynamic execution (not hardcoded)
- Accumulate context from tool results

**Difference from Structured:**
- Structured: Only executes `retrieve_tool`
- Agentic: Executes any tool based on LLM's decision

---

### **STEP 4: Reasoning Node** ✅

**What we did:**
```python
def reasoning_node(state: AgenticState) -> AgenticState:
    # LLM evaluates if answer is complete
    prompt = f"""
    Question: {question}
    Context: {len(context)} documents
    Answer: {answer}
    
    Is answer complete? Should I continue, refine, or end?
    """
    response = decision_llm.invoke(prompt)
    # Returns: "continue", "refine", or "end"
    state["should_continue"] = decision
```

**Why:**
- **AGENTIC**: LLM reasons about next steps
- Enables iterative refinement
- Knows when to stop

**Difference from Structured:**
- Structured: Always goes to generate (no reasoning)
- Agentic: LLM decides if need more info or can end

**Example Reasoning:**
- "Have 2 docs, answer is complete" → `end`
- "Have 1 doc, answer incomplete" → `continue` (get more)
- "Have answer but could be better" → `refine` (improve)

---

### **STEP 5: Conditional Routing Function** ✅

**What we did:**
```python
def should_continue(state: AgenticState) -> Literal["tool_selection", "generate", "end"]:
    decision = state["should_continue"]
    
    if decision == "continue":
        return "tool_selection"  # Loop back to get more info
    elif decision == "refine":
        return "tool_selection"  # Loop back to improve
    else:  # "end"
        return "generate"  # Generate final answer
```

**Why:**
- **AGENTIC**: Routes based on LLM's decision
- Enables dynamic flow (not fixed)
- Allows looping back

**Difference from Structured:**
- Structured: Fixed edges (always same path)
- Agentic: Conditional edges (path changes based on decision)

**Flow Visualization:**
```
reasoning_node
    ↓
should_continue() function
    ↓
    ├─→ "continue" → tool_selection (loop back)
    ├─→ "refine" → tool_selection (loop back)
    └─→ "end" → generate (finalize)
```

---

### **STEP 6: Build Graph with Conditional Edges** ✅

**What we did:**
```python
def build_agentic_graph():
    graph = StateGraph(AgenticState)
    
    # Add nodes
    graph.add_node("tool_selection", tool_selection_node)
    graph.add_node("tool_execution", tool_execution_node)
    graph.add_node("reasoning", reasoning_node)
    graph.add_node("generate", generate_answer_node)
    
    # Fixed edges
    graph.add_edge("tool_selection", "tool_execution")
    graph.add_edge("tool_execution", "reasoning")
    
    # AGENTIC: Conditional routing
    graph.add_conditional_edges(
        "reasoning",
        should_continue,  # Function that decides next node
        {
            "tool_selection": "tool_selection",  # Can loop back!
            "generate": "generate",
            "end": END
        }
    )
    
    graph.add_edge("generate", END)
```

**Why:**
- Conditional edges enable dynamic routing
- Can loop back (iterative refinement)
- LLM controls the flow

**Difference from Structured:**
- Structured: All edges are fixed (`add_edge`)
- Agentic: Uses conditional edges (`add_conditional_edges`)

**Key Difference:**
```python
# Structured (fixed):
graph.add_edge("retrieve", "generate")  # Always goes here

# Agentic (conditional):
graph.add_conditional_edges(
    "reasoning",
    should_continue,  # LLM decides!
    {"tool_selection": "tool_selection", "generate": "generate"}
)
```

---

## 🔄 Complete Agentic Flow

### Execution Example:

```
1. START
   ↓
2. tool_selection_node
   - LLM: "Question needs semantic search"
   - Decision: retrieve_tool
   ↓
3. tool_execution_node
   - Execute: retrieve_tool
   - Result: 3 documents
   ↓
4. reasoning_node
   - LLM: "Have 3 docs, but answer incomplete"
   - Decision: continue
   ↓
5. should_continue() → "tool_selection" (LOOP BACK!)
   ↓
6. tool_selection_node (iteration 2)
   - LLM: "Need keyword search for specific term"
   - Decision: keyword_search_tool
   ↓
7. tool_execution_node
   - Execute: keyword_search_tool
   - Result: 2 more documents
   ↓
8. reasoning_node
   - LLM: "Have 5 docs total, answer is complete"
   - Decision: end
   ↓
9. should_continue() → "generate"
   ↓
10. generate_answer_node
    - Generate answer from all 5 documents
    ↓
11. END
```

---

## 🎯 Key Agentic Features Implemented

### ✅ 1. LLM-Based Tool Selection
- LLM analyzes question
- Chooses appropriate tool
- Not hardcoded

### ✅ 2. Dynamic Tool Execution
- Executes whatever tool LLM selected
- Can use any available tool
- Accumulates context

### ✅ 3. Reasoning About Next Steps
- LLM evaluates completeness
- Decides: continue/refine/end
- Prevents infinite loops

### ✅ 4. Conditional Routing
- Path changes based on LLM decision
- Can loop back
- Dynamic flow

### ✅ 5. Iterative Refinement
- Can gather info in multiple steps
- Can refine answer quality
- Handles complex queries

---

## 📊 Comparison Table

| Feature | Structured RAG | Agentic RAG |
|---------|---------------|-------------|
| **Tool Selection** | Hardcoded | ✅ LLM decides |
| **Routing** | Fixed edges | ✅ Conditional edges |
| **Iteration** | Single pass | ✅ Can loop back |
| **Reasoning** | None | ✅ LLM reasons |
| **Flow** | Deterministic | ✅ Dynamic |
| **Adaptability** | Low | ✅ High |

---

## 🚀 Result

**You now have a fully agentic RAG system!**

The LLM:
- ✅ Decides which tools to use
- ✅ Reasons about next steps
- ✅ Routes dynamically
- ✅ Can refine iteratively
- ✅ Adapts to question type

This is **true agentic behavior**! 🎉

