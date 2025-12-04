# Building Agentic Flow - Interactive Step-by-Step Guide

## 🎯 What We're Building

A **fully agentic RAG system** where the LLM makes decisions about:
1. **Which tools to use** (not hardcoded)
2. **When to continue/refine/end** (reasoning)
3. **How to route** (conditional, not fixed)

---

## 📋 Step-by-Step Build Process

### **STEP 1: Enhanced Agent State** ✅

**What we're doing:**
Adding new fields to track agent decisions and state.

**Code:**
```python
class AgenticState(TypedDict):
    session_id: str
    question: str
    context: List[str]
    answer: str
    # NEW FIELDS FOR AGENTIC:
    tool_selection: Optional[str]      # Which tool LLM selected
    tool_results: Optional[dict]       # Results from tool execution
    reasoning: Optional[str]           # LLM's reasoning
    iteration_count: int               # Prevent infinite loops
    should_continue: Optional[Literal["continue", "refine", "end"]]  # Routing decision
```

**Why this matters:**
- **Structured RAG**: Only tracks `question`, `context`, `answer`
- **Agentic**: Tracks decisions, tool usage, reasoning, iterations
- **Enables**: Dynamic routing and iterative refinement

**Explanation:**
In structured RAG, the flow is fixed, so we don't need to track decisions. In agentic, the LLM makes decisions at each step, so we need to track:
- What tool was selected (for debugging/logging)
- What the reasoning was (to understand agent's thinking)
- How many iterations (to prevent infinite loops)
- What the routing decision is (to know where to go next)

---

### **STEP 2: Tool Selection Node** ✅

**What we're doing:**
Creating a node where the LLM decides which tool to use.

**Code:**
```python
def tool_selection_node(state: AgenticState) -> AgenticState:
    question = state["question"]
    
    # Build prompt asking LLM to choose a tool
    prompt = f"""
    Question: {question}
    Available tools:
    1. retrieve_tool - Semantic search
    2. keyword_search_tool - Exact keyword match
    3. metadata_search_tool - Filter by metadata
    4. summarize_tool - Summarize context
    
    Which tool should I use?
    """
    
    # LLM makes the decision
    response = agent_llm.invoke(prompt).content
    tool_name = parse_tool_name(response)
    
    state["tool_selection"] = tool_name
    return state
```

**Why this is agentic:**
- **Structured RAG**: Always uses `retrieve_tool` (hardcoded)
- **Agentic**: LLM analyzes question and chooses tool
- **Result**: Different tools for different question types

**Example decisions:**
- "What is SIM provisioning?" → `retrieve_tool` (semantic search)
- "Find docs with topic=circuit_breaker" → `metadata_search_tool` (metadata filter)
- "Search for 'retry mechanism'" → `keyword_search_tool` (exact match)

**Interactive explanation:**
The LLM acts like a smart assistant that looks at your question and thinks: "Hmm, this question needs semantic understanding, so I'll use retrieve_tool" or "This is asking for a specific category, so I'll use metadata_search_tool". This is **decision-making**, which is what makes it agentic!

---

### **STEP 3: Tool Execution Node** ✅

**What we're doing:**
Executing the tool that the LLM selected (dynamically).

**Code:**
```python
def tool_execution_node(state: AgenticState) -> AgenticState:
    tool_name = state["tool_selection"]  # Get LLM's choice
    
    # Dynamically execute based on selection
    if tool_name == "retrieve_tool":
        result = retrieve_tool(question)
    elif tool_name == "keyword_search_tool":
        result = keyword_search_tool(keyword)
    elif tool_name == "metadata_search_tool":
        result = metadata_search_tool(key, value)
    elif tool_name == "summarize_tool":
        result = summarize_tool(context)
    
    # Accumulate results
    state["context"] = current_context + result["results"]
    return state
```

**Why this is agentic:**
- **Structured RAG**: Only executes `retrieve_tool` (hardcoded)
- **Agentic**: Executes whatever tool LLM selected (dynamic)
- **Result**: Can use different tools based on question

**Interactive explanation:**
Think of this like a toolbox. In structured RAG, you always grab the hammer (retrieve_tool). In agentic, the LLM looks at the job and says "I need a screwdriver" (keyword_search_tool) or "I need a wrench" (metadata_search_tool), and then uses that tool. The execution is **dynamic** based on the decision!

---

### **STEP 4: Reasoning Node** ✅

**What we're doing:**
LLM evaluates if the answer is complete or needs more information.

**Code:**
```python
def reasoning_node(state: AgenticState) -> AgenticState:
    question = state["question"]
    context = state.get("context", [])
    answer = state.get("answer", "")
    
    # LLM reasons about next steps
    prompt = f"""
    Question: {question}
    Context: {len(context)} documents
    Answer: {answer}
    
    Is answer complete? Should I:
    - "continue" (need more info)
    - "refine" (answer exists but needs improvement)
    - "end" (answer is complete)
    """
    
    response = decision_llm.invoke(prompt).content
    decision = parse_decision(response)  # "continue", "refine", or "end"
    
    state["should_continue"] = decision
    state["reasoning"] = "LLM's explanation"
    return state
```

**Why this is agentic:**
- **Structured RAG**: Always goes to generate (no reasoning)
- **Agentic**: LLM reasons about completeness
- **Result**: Can loop back to get more info or refine

**Interactive explanation:**
This is like the LLM asking itself: "Do I have enough information to answer this question?" If yes → end. If no → continue (get more info). If answer exists but could be better → refine (improve it). This is **reasoning**, which enables iterative refinement!

**Example reasoning:**
- "Have 2 docs about circuit breaker, but question asks about A1 protection too" → `continue` (need more info about A1)
- "Have 5 docs, answer is complete" → `end` (ready to generate)
- "Have answer but it's vague" → `refine` (get more specific docs)

---

### **STEP 5: Conditional Routing Function** ✅

**What we're doing:**
Creating a function that routes based on LLM's decision.

**Code:**
```python
def should_continue(state: AgenticState) -> Literal["tool_selection", "generate", "end"]:
    """
    AGENTIC: Routes based on LLM's decision.
    This is the KEY difference - path changes dynamically!
    """
    decision = state.get("should_continue", "end")
    iteration = state.get("iteration_count", 0)
    
    # Safety: prevent infinite loops
    if iteration >= 3:
        return "end"
    
    if decision == "continue":
        return "tool_selection"  # Loop back to get more info
    elif decision == "refine":
        return "tool_selection"  # Loop back to improve
    else:  # "end"
        return "generate"  # Generate final answer
```

**Why this is agentic:**
- **Structured RAG**: Fixed edges (always same path)
- **Agentic**: Conditional routing (path changes based on decision)
- **Result**: Can loop back, enabling iterative refinement

**Interactive explanation:**
This is the **traffic controller** of the agentic system. In structured RAG, it's like a one-way street (always same route). In agentic, it's like a smart traffic light that changes based on conditions:
- If LLM says "continue" → Route back to tool_selection (get more info)
- If LLM says "refine" → Route back to tool_selection (improve answer)
- If LLM says "end" → Route to generate (finalize)

This enables **looping back**, which is crucial for iterative refinement!

---

### **STEP 6: Build Graph with Conditional Edges** ✅

**What we're doing:**
Creating the graph with conditional routing (not fixed edges).

**Code:**
```python
def build_agentic_graph():
    graph = StateGraph(AgenticState)
    
    # Add nodes
    graph.add_node("tool_selection", tool_selection_node)
    graph.add_node("tool_execution", tool_execution_node)
    graph.add_node("reasoning", reasoning_node)
    graph.add_node("generate", generate_answer_node)
    
    # Set entry point
    graph.set_entry_point("tool_selection")
    
    # Fixed edges (within a cycle)
    graph.add_edge("tool_selection", "tool_execution")
    graph.add_edge("tool_execution", "reasoning")
    
    # AGENTIC: Conditional routing (can loop back!)
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
    return graph.compile()
```

**Why this is agentic:**
- **Structured RAG**: All edges are fixed (`add_edge`)
- **Agentic**: Uses conditional edges (`add_conditional_edges`)
- **Result**: Dynamic flow that can loop back

**Visual comparison:**

**Structured RAG (Fixed):**
```
decompose → retrieve → rerank → generate → END
(always same path, no loops)
```

**Agentic RAG (Dynamic):**
```
tool_selection → tool_execution → reasoning
                    ↑                    ↓
                    └── [can loop back] ─┘
                                    ↓
                                generate → END
```

**Interactive explanation:**
The graph structure is fundamentally different:
- **Structured**: Linear pipeline (one-way flow)
- **Agentic**: Graph with cycles (can loop back)

The `add_conditional_edges` is the key - it allows the graph to route dynamically based on the `should_continue` function, which uses the LLM's decision. This is what enables **iterative refinement**!

---

## 🔄 Complete Flow Example

### Example: Complex Question (Multiple Iterations)

**Question**: "Compare circuit breaker and load balancing"

**Iteration 1:**
```
1. tool_selection_node
   LLM: "Need info about circuit breaker"
   Decision: retrieve_tool
   
2. tool_execution_node
   Execute: retrieve_tool("circuit breaker")
   Result: 3 documents about circuit breaker
   
3. reasoning_node
   LLM: "Have circuit breaker info, but need load balancing too"
   Decision: continue
   
4. should_continue() → "tool_selection" (LOOP BACK!)
```

**Iteration 2:**
```
5. tool_selection_node (iteration 2)
   LLM: "Need info about load balancing"
   Decision: retrieve_tool
   
6. tool_execution_node
   Execute: retrieve_tool("load balancing")
   Result: 3 documents about load balancing
   
7. reasoning_node
   LLM: "Have both topics, can compare now"
   Decision: end
   
8. should_continue() → "generate"
```

**Iteration 3:**
```
9. generate_answer_node
   Generate: "Circuit breaker... Load balancing... Comparison..."
   
10. END
```

**Total iterations**: 2 tool selections, 1 generation

---

## 🎯 Key Agentic Features

### ✅ 1. LLM-Based Tool Selection
- **What**: LLM chooses which tool to use
- **Why**: Different questions need different tools
- **Example**: Semantic search vs keyword search vs metadata filter

### ✅ 2. Dynamic Tool Execution
- **What**: Execute whatever tool LLM selected
- **Why**: Not hardcoded, adapts to question
- **Example**: Can use any of 4 tools based on decision

### ✅ 3. Reasoning About Next Steps
- **What**: LLM evaluates if answer is complete
- **Why**: Knows when to stop or continue
- **Example**: "Have enough info? Yes → end, No → continue"

### ✅ 4. Conditional Routing
- **What**: Route based on LLM's decision
- **Why**: Enables dynamic flow
- **Example**: Continue if need more, end if have enough

### ✅ 5. Iterative Refinement
- **What**: Can loop back to improve answer
- **Why**: Complex questions need multiple steps
- **Example**: Get info about A, then B, then compare

---

## 📊 Comparison: Structured vs Agentic

| Aspect | Structured RAG | Agentic RAG |
|--------|---------------|-------------|
| **Tool Selection** | Hardcoded (always retrieve) | ✅ LLM decides |
| **Routing** | Fixed edges | ✅ Conditional edges |
| **Iteration** | Single pass | ✅ Can loop back |
| **Reasoning** | None | ✅ LLM reasons |
| **Flow** | Deterministic | ✅ Dynamic |
| **Adaptability** | Low | ✅ High |
| **Complex Queries** | Limited | ✅ Handles well |

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

