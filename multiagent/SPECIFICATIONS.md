# 📋 Multi-Agent System Specifications

## 📋 Table of Contents

1. [Agent Specifications](#agent-specifications)
2. [Workflow Specifications](#workflow-specifications)
3. [State Specifications](#state-specifications)
4. [API Specifications](#api-specifications)
5. [Example Scenarios](#example-scenarios)

---

## 🤖 Agent Specifications

### 1. Research Agent

**Name**: `ResearchAgent`

**Purpose**: Gather comprehensive information from documents

**Input**:
```python
{
    "question": str,
    "context": List[str],  # Existing context (may be empty)
    "session_id": str
}
```

**Processing**:
1. Analyze question to determine search strategy
2. Use `retrieve_tool` for semantic search
3. Use `keyword_search_tool` for specific terms
4. Use `metadata_search_tool` if metadata filtering needed
5. Combine all retrieved documents
6. Deduplicate results

**Output**:
```python
{
    "research_context": List[str],  # Retrieved documents
    "search_strategy": str,  # Which tools were used
    "doc_count": int,  # Number of documents retrieved
    "metadata": {
        "tools_used": List[str],
        "retrieval_time": float
    }
}
```

**LLM Model**: `gpt-4o-mini` (fast, cost-effective for retrieval decisions)

**Error Handling**:
- If no documents found, return empty list with warning
- If tool fails, try alternative tool
- Log all errors for debugging

---

### 2. Analysis Agent

**Name**: `AnalysisAgent`

**Purpose**: Analyze and structure gathered information

**Input**:
```python
{
    "question": str,
    "research_context": List[str],  # From Research Agent
    "session_id": str
}
```

**Processing**:
1. If context is too long (>5000 chars), use `summarize_tool`
2. Analyze documents for key points
3. Extract relevant information
4. Structure information logically
5. Identify relationships and patterns
6. Filter irrelevant content

**Output**:
```python
{
    "analyzed_info": str,  # Structured analysis
    "key_points": List[str],  # Extracted key points
    "relationships": List[str],  # Identified relationships
    "metadata": {
        "original_doc_count": int,
        "analysis_time": float,
        "was_summarized": bool
    }
}
```

**LLM Model**: `gpt-4o` (needs reasoning capability)

**Prompt Template**:
```
You are an analysis agent. Analyze the following documents and extract:
1. Key points relevant to the question
2. Important relationships
3. Structured information

Question: {question}
Documents: {research_context}

Provide a structured analysis.
```

---

### 3. Synthesis Agent

**Name**: `SynthesisAgent`

**Purpose**: Combine analyzed information into final answer

**Input**:
```python
{
    "question": str,
    "analyzed_info": str,  # From Analysis Agent
    "research_context": List[str],  # Original context (for reference)
    "session_id": str
}
```

**Processing**:
1. Review analyzed information
2. Synthesize into coherent answer
3. Ensure completeness
4. Format appropriately
5. Add citations if needed

**Output**:
```python
{
    "final_answer": str,  # Complete answer
    "confidence": float,  # 0.0-1.0
    "citations": List[str],  # Source references
    "metadata": {
        "synthesis_time": float,
        "answer_length": int
    }
}
```

**LLM Model**: `gpt-4o` (needs high quality generation)

**Prompt Template**:
```
You are a synthesis agent. Create a comprehensive answer based on the analyzed information.

Question: {question}
Analyzed Information: {analyzed_info}

Provide a clear, complete, and well-structured answer.
```

---

### 4. Evaluator Agent

**Name**: `EvaluatorAgent`

**Purpose**: Evaluate and compare multiple answers

**Input**:
```python
{
    "question": str,
    "candidate_answers": Dict[str, str],  # {agent_name: answer}
    "session_id": str
}
```

**Processing**:
1. Evaluate each answer on multiple criteria:
   - Relevance to question
   - Completeness
   - Accuracy (if verifiable)
   - Clarity
   - Usefulness
2. Score each answer (0.0-1.0)
3. Select best answer
4. Provide reasoning

**Output**:
```python
{
    "selected_answer": str,  # Best answer
    "selected_agent": str,  # Which agent produced it
    "evaluation_scores": Dict[str, float],  # {agent_name: score}
    "reasoning": str,  # Why this answer was selected
    "metadata": {
        "evaluation_time": float,
        "criteria_used": List[str]
    }
}
```

**LLM Model**: `gpt-4o` (needs evaluation capability)

**Evaluation Criteria**:
1. **Relevance** (0.0-1.0): How well does it answer the question?
2. **Completeness** (0.0-1.0): Does it cover all aspects?
3. **Clarity** (0.0-1.0): Is it easy to understand?
4. **Usefulness** (0.0-1.0): Is it actionable/helpful?

**Prompt Template**:
```
You are an evaluator agent. Evaluate the following answers and select the best one.

Question: {question}
Answers:
{formatted_answers}

Evaluate each answer on:
1. Relevance
2. Completeness
3. Clarity
4. Usefulness

Select the best answer and provide reasoning.
```

---

### 5. Supervisor Agent

**Name**: `SupervisorAgent`

**Purpose**: Coordinate and delegate tasks to workers

**Input**:
```python
{
    "question": str,
    "session_id": str
}
```

**Processing**:
1. Analyze question complexity
2. Determine required workers
3. Create task plan
4. Delegate tasks to workers
5. Wait for worker results
6. Combine results
7. Generate final answer

**Output**:
```python
{
    "supervisor_plan": str,  # Task plan
    "workers_used": List[str],  # Which workers were used
    "worker_results": Dict[str, Any],  # {worker_name: result}
    "combined_result": str,  # Combined answer
    "final_answer": str,  # Final formatted answer
    "metadata": {
        "planning_time": float,
        "total_time": float
    }
}
```

**LLM Model**: `gpt-4o` (needs planning capability)

**Available Workers**:
- `RetrievalWorker`: Document retrieval
- `AnalysisWorker`: Information analysis
- `CodeWorker`: Code-related queries
- `ComparisonWorker`: Compare multiple topics
- `ExplanationWorker`: Conceptual explanations

**Prompt Template**:
```
You are a supervisor agent. Analyze the question and create a task plan.

Question: {question}

Available workers:
- RetrievalWorker: Document retrieval
- AnalysisWorker: Information analysis
- CodeWorker: Code-related queries
- ComparisonWorker: Compare multiple topics
- ExplanationWorker: Conceptual explanations

Create a plan: which workers to use and what tasks to assign.
```

---

## 🔄 Workflow Specifications

### Workflow 1: Sequential Pipeline

**Name**: `sequential_workflow`

**Graph Structure**:
```python
graph = StateGraph(MultiAgentState)
graph.add_node("research", research_agent_node)
graph.add_node("analysis", analysis_agent_node)
graph.add_node("synthesis", synthesis_agent_node)

graph.set_entry_point("research")
graph.add_edge("research", "analysis")
graph.add_edge("analysis", "synthesis")
graph.add_edge("synthesis", END)
```

**State Flow**:
```
Initial State
    → research_node
        → state.research_context = [...]
        → state.context = [...]
    → analysis_node
        → state.analyzed_info = "..."
    → synthesis_node
        → state.final_answer = "..."
    → END
```

**Error Handling**:
- If research fails, return error immediately
- If analysis fails, use raw research context
- If synthesis fails, return analyzed info as answer

**Timeout**: 60 seconds total

---

### Workflow 2: Parallel Competitive

**Name**: `parallel_workflow`

**Graph Structure**:
```python
graph = StateGraph(MultiAgentState)
graph.add_node("structured_rag", structured_rag_node)
graph.add_node("agentic_rag", agentic_rag_node)
graph.add_node("research_agent", research_agent_node)
graph.add_node("evaluator", evaluator_agent_node)

graph.set_entry_point("parallel_branch")
graph.add_conditional_edges(
    "parallel_branch",
    route_to_parallel_agents
)
graph.add_edge("structured_rag", "evaluator")
graph.add_edge("agentic_rag", "evaluator")
graph.add_edge("research_agent", "evaluator")
graph.add_edge("evaluator", END)
```

**State Flow**:
```
Initial State
    → parallel_branch
        → structured_rag_node (async)
        → agentic_rag_node (async)
        → research_agent_node (async)
    → All complete, state.candidate_answers = {...}
    → evaluator_node
        → state.selected_answer = "..."
        → state.evaluation_scores = {...}
    → END
```

**Parallel Execution**:
- Use `asyncio.gather()` for parallel execution
- Wait for all agents to complete
- Collect all results before evaluation

**Error Handling**:
- If one agent fails, continue with others
- Evaluator handles partial results
- Log all errors

**Timeout**: 90 seconds total (30s per agent max)

---

### Workflow 3: Supervisor-Worker

**Name**: `supervisor_workflow`

**Graph Structure**:
```python
graph = StateGraph(MultiAgentState)
graph.add_node("supervisor", supervisor_agent_node)
graph.add_node("retrieval_worker", retrieval_worker_node)
graph.add_node("analysis_worker", analysis_worker_node)
graph.add_node("code_worker", code_worker_node)
graph.add_node("combine", supervisor_combine_node)

graph.set_entry_point("supervisor")
graph.add_conditional_edges(
    "supervisor",
    route_to_workers
)
graph.add_edge("retrieval_worker", "combine")
graph.add_edge("analysis_worker", "combine")
graph.add_edge("code_worker", "combine")
graph.add_edge("combine", END)
```

**State Flow**:
```
Initial State
    → supervisor_node
        → state.supervisor_plan = "..."
        → state.workers_used = [...]
    → delegate_to_workers (parallel)
        → retrieval_worker_node
        → analysis_worker_node
        → code_worker_node
    → All complete, state.worker_results = {...}
    → combine_node
        → state.combined_result = "..."
        → state.final_answer = "..."
    → END
```

**Dynamic Routing**:
- Supervisor decides which workers to use
- Only selected workers execute
- Results combined by supervisor

**Error Handling**:
- If supervisor fails, use default workers
- If worker fails, supervisor handles gracefully
- Log all errors

**Timeout**: 120 seconds total

---

## 📦 State Specifications

### MultiAgentState

```python
from typing import TypedDict, List, Dict, Optional, Literal, Any

class MultiAgentState(TypedDict):
    # Core fields (always present)
    session_id: str
    question: str
    final_answer: str
    pattern: Literal["sequential", "parallel", "supervisor"]
    
    # Sequential pattern fields
    research_context: Optional[List[str]]
    analyzed_info: Optional[str]
    
    # Parallel pattern fields
    candidate_answers: Optional[Dict[str, str]]  # {agent_name: answer}
    evaluation_scores: Optional[Dict[str, float]]  # {agent_name: score}
    selected_answer: Optional[str]
    selected_agent: Optional[str]
    
    # Supervisor pattern fields
    supervisor_plan: Optional[str]
    workers_used: Optional[List[str]]
    worker_results: Optional[Dict[str, Any]]  # {worker_name: result}
    combined_result: Optional[str]
    
    # Common fields
    context: List[str]  # Accumulated context
    metadata: Dict[str, Any]  # Additional metadata
    error: Optional[str]  # Error message if any
    iteration_count: int  # Track iterations
    execution_time: float  # Total execution time
```

### State Initialization

```python
def create_initial_state(
    question: str,
    session_id: str,
    pattern: Literal["sequential", "parallel", "supervisor"]
) -> MultiAgentState:
    return {
        "session_id": session_id,
        "question": question,
        "final_answer": "",
        "pattern": pattern,
        "research_context": None,
        "analyzed_info": None,
        "candidate_answers": None,
        "evaluation_scores": None,
        "selected_answer": None,
        "selected_agent": None,
        "supervisor_plan": None,
        "workers_used": None,
        "worker_results": None,
        "combined_result": None,
        "context": [],
        "metadata": {},
        "error": None,
        "iteration_count": 0,
        "execution_time": 0.0
    }
```

---

## 🌐 API Specifications

### Endpoint 1: Sequential Multi-Agent

**POST** `/multiagent/sequential/chat`

**Request**:
```json
{
    "question": "What is a circuit breaker?",
    "session_id": "session_123"
}
```

**Response**:
```json
{
    "answer": "A circuit breaker is...",
    "pattern": "sequential",
    "metadata": {
        "research_context_count": 5,
        "analysis_time": 1.2,
        "synthesis_time": 0.8,
        "total_time": 3.5
    },
    "session_id": "session_123"
}
```

---

### Endpoint 2: Parallel Multi-Agent

**POST** `/multiagent/parallel/chat`

**Request**:
```json
{
    "question": "What is a circuit breaker?",
    "session_id": "session_123"
}
```

**Response**:
```json
{
    "answer": "A circuit breaker is...",
    "pattern": "parallel",
    "selected_agent": "agentic_rag",
    "evaluation_scores": {
        "structured_rag": 0.85,
        "agentic_rag": 0.92,
        "research_agent": 0.78
    },
    "metadata": {
        "total_time": 4.2,
        "evaluation_reasoning": "Agentic RAG provided most complete answer..."
    },
    "session_id": "session_123"
}
```

---

### Endpoint 3: Supervisor-Worker

**POST** `/multiagent/supervisor/chat`

**Request**:
```json
{
    "question": "Explain how to implement circuit breaker pattern in microservices",
    "session_id": "session_123"
}
```

**Response**:
```json
{
    "answer": "To implement a circuit breaker pattern...",
    "pattern": "supervisor",
    "supervisor_plan": "Use RetrievalWorker for docs, CodeWorker for examples, AnalysisWorker for best practices",
    "workers_used": ["retrieval_worker", "code_worker", "analysis_worker"],
    "metadata": {
        "planning_time": 0.5,
        "execution_time": 5.3,
        "total_time": 5.8
    },
    "session_id": "session_123"
}
```

---

### Endpoint 4: Auto-Select Pattern

**POST** `/multiagent/chat`

**Request**:
```json
{
    "question": "What is a circuit breaker?",
    "session_id": "session_123",
    "auto_select_pattern": true
}
```

**Response**:
```json
{
    "answer": "...",
    "pattern": "sequential",  // Auto-selected based on question
    "pattern_selection_reasoning": "Question is straightforward, sequential pattern is sufficient",
    "metadata": {...}
}
```

---

## 📝 Example Scenarios

### Scenario 1: Simple Question (Sequential)

**Question**: "What is a circuit breaker?"

**Flow**:
1. Research Agent: Retrieves 5 documents about circuit breakers
2. Analysis Agent: Extracts key points about definition, purpose, types
3. Synthesis Agent: Creates comprehensive answer

**Expected Answer**: Clear definition with key characteristics

---

### Scenario 2: Comparison Question (Sequential)

**Question**: "Compare circuit breakers and load balancing"

**Flow**:
1. Research Agent: Retrieves docs on both topics (10 documents)
2. Analysis Agent: Identifies similarities, differences, use cases
3. Synthesis Agent: Creates structured comparison

**Expected Answer**: Side-by-side comparison with similarities and differences

---

### Scenario 3: Best Answer Selection (Parallel)

**Question**: "What is a circuit breaker?"

**Flow**:
1. Structured RAG: Generates answer A
2. Agentic RAG: Generates answer B
3. Research Agent: Generates answer C
4. Evaluator: Compares all, selects best (answer B)

**Expected Answer**: Best answer from all approaches

---

### Scenario 4: Complex Multi-Domain (Supervisor-Worker)

**Question**: "Explain how to implement circuit breaker pattern in microservices with code examples"

**Flow**:
1. Supervisor: Analyzes question, decides to use:
   - RetrievalWorker: Get architecture docs
   - CodeWorker: Get code examples
   - AnalysisWorker: Get best practices
2. Workers execute in parallel
3. Supervisor combines results into comprehensive answer

**Expected Answer**: Complete guide with architecture, code, and best practices

---

## ✅ Validation Criteria

### Functional Requirements
- [ ] All three patterns work correctly
- [ ] Agents produce expected outputs
- [ ] State transitions work properly
- [ ] Error handling works
- [ ] Timeouts are respected

### Performance Requirements
- [ ] Sequential: < 10 seconds
- [ ] Parallel: < 15 seconds
- [ ] Supervisor: < 20 seconds
- [ ] Memory usage < 500MB per request

### Quality Requirements
- [ ] Answers are relevant and complete
- [ ] Evaluation scores are meaningful
- [ ] Error messages are clear
- [ ] Logging is comprehensive

---

## 🔍 Review Checklist

Before starting development, review:

- [ ] Agent specifications are clear
- [ ] Workflow specifications are complete
- [ ] State management is well-defined
- [ ] API specifications match requirements
- [ ] Example scenarios are realistic
- [ ] Error handling is comprehensive
- [ ] Performance requirements are reasonable

---

## 📚 Next Steps

1. Review all specifications
2. Provide feedback
3. Approve for development
4. Start Phase 1 implementation

