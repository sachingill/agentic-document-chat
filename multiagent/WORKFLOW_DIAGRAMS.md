# 📊 Multi-Agent Workflow Diagrams

## Visual Representations of All Workflow Patterns

---

## Pattern 1: Sequential Pipeline

### Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    User Question                             │
│              "What is a circuit breaker?"                    │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────┐
        │      Research Agent Node          │
        │  ┌─────────────────────────────┐  │
        │  │ 1. Analyze question         │  │
        │  │ 2. Use retrieve_tool        │  │
        │  │ 3. Use keyword_search_tool  │  │
        │  │ 4. Collect documents        │  │
        │  └─────────────────────────────┘  │
        └───────────────┬───────────────────┘
                        │
                        ▼
        State: research_context = [doc1, doc2, doc3, ...]
                        │
                        ▼
        ┌───────────────────────────────────┐
        │      Analysis Agent Node          │
        │  ┌─────────────────────────────┐  │
        │  │ 1. Read research_context    │  │
        │  │ 2. Extract key points       │  │
        │  │ 3. Identify relationships   │  │
        │  │ 4. Structure information    │  │
        │  └─────────────────────────────┘  │
        └───────────────┬───────────────────┘
                        │
                        ▼
        State: analyzed_info = "Structured analysis..."
                        │
                        ▼
        ┌───────────────────────────────────┐
        │      Synthesis Agent Node         │
        │  ┌─────────────────────────────┐  │
        │  │ 1. Read analyzed_info       │  │
        │  │ 2. Synthesize answer        │  │
        │  │ 3. Format response          │  │
        │  │ 4. Add citations            │  │
        │  └─────────────────────────────┘  │
        └───────────────┬───────────────────┘
                        │
                        ▼
        State: final_answer = "A circuit breaker is..."
                        │
                        ▼
                ┌───────────────┐
                │      END      │
                └───────────────┘
```

### State Transition Diagram

```
Initial State
    │
    │ question: "What is a circuit breaker?"
    │ research_context: None
    │ analyzed_info: None
    │ final_answer: ""
    │
    ▼
┌─────────────────┐
│  Research Node  │
└────────┬────────┘
    │
    │ research_context: [doc1, doc2, doc3]
    │ context: [doc1, doc2, doc3]
    │
    ▼
┌─────────────────┐
│  Analysis Node  │
└────────┬────────┘
    │
    │ analyzed_info: "Key points: ..."
    │
    ▼
┌─────────────────┐
│ Synthesis Node  │
└────────┬────────┘
    │
    │ final_answer: "A circuit breaker is..."
    │
    ▼
     END
```

---

## Pattern 2: Parallel Competitive

### Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    User Question                             │
│              "What is a circuit breaker?"                    │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────┐
        │      Parallel Branch Node         │
        │    (Routes to all agents)         │
        └───────┬───────┬───────┬───────────┘
                │       │       │
        ┌───────▼───┐ ┌─▼──────┐ ┌─▼──────────┐
        │Structured │ │Agentic │ │  Research  │
        │RAG Agent  │ │RAG     │ │  Agent     │
        │           │ │Agent   │ │            │
        │           │ │        │ │            │
        │ Answer A  │ │Answer B│ │  Answer C  │
        └───────┬───┘ └───┬────┘ └─────┬──────┘
                │         │            │
                └─────────┼────────────┘
                          │
                          ▼
        State: candidate_answers = {
            "structured_rag": "Answer A...",
            "agentic_rag": "Answer B...",
            "research_agent": "Answer C..."
        }
                          │
                          ▼
        ┌───────────────────────────────────┐
        │      Evaluator Agent Node         │
        │  ┌─────────────────────────────┐  │
        │  │ 1. Read all answers         │  │
        │  │ 2. Score each answer        │  │
        │  │    - Relevance: 0.0-1.0     │  │
        │  │    - Completeness: 0.0-1.0  │  │
        │  │    - Clarity: 0.0-1.0       │  │
        │  │    - Usefulness: 0.0-1.0    │  │
        │  │ 3. Select best answer       │  │
        │  │ 4. Provide reasoning        │  │
        │  └─────────────────────────────┘  │
        └───────────────┬───────────────────┘
                        │
                        ▼
        State: selected_answer = "Answer B..."
        State: selected_agent = "agentic_rag"
        State: evaluation_scores = {
            "structured_rag": 0.85,
            "agentic_rag": 0.92,
            "research_agent": 0.78
        }
                        │
                        ▼
                ┌───────────────┐
                │      END      │
                └───────────────┘
```

### Parallel Execution Timeline

```
Time →
     │
     ├─ Structured RAG Agent ──────────────┐
     │                                      │
     ├─ Agentic RAG Agent ─────────────────┤
     │                                      │
     ├─ Research Agent ────────────────────┤
     │                                      │
     │                                      ▼
     │                            All Complete
     │                                      │
     │                                      ▼
     │                            Evaluator Agent
     │                                      │
     │                                      ▼
     │                                    END
```

---

## Pattern 3: Supervisor-Worker

### Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    User Question                             │
│  "Explain circuit breaker implementation in microservices"   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────┐
        │      Supervisor Agent Node        │
        │  ┌─────────────────────────────┐  │
        │  │ 1. Analyze question         │  │
        │  │ 2. Determine required       │  │
        │  │    workers                  │  │
        │  │ 3. Create task plan         │  │
        │  │ 4. Delegate tasks           │  │
        │  └─────────────────────────────┘  │
        └───────────────┬───────────────────┘
                        │
                        ▼
        State: supervisor_plan = "Use RetrievalWorker, CodeWorker, AnalysisWorker"
        State: workers_used = ["retrieval_worker", "code_worker", "analysis_worker"]
                        │
                        ▼
        ┌───────────────────────────────────┐
        │      Worker Delegation            │
        │    (Parallel Execution)           │
        └───────┬───────┬───────┬───────────┘
                │       │       │
        ┌───────▼───┐ ┌─▼──────┐ ┌─▼──────────┐
        │Retrieval  │ │  Code  │ │  Analysis  │
        │  Worker   │ │ Worker │ │   Worker   │
        │           │ │        │ │            │
        │  Docs     │ │Examples│ │Best        │
        │           │ │        │ │Practices   │
        └───────┬───┘ └───┬────┘ └─────┬──────┘
                │         │            │
                └─────────┼────────────┘
                          │
                          ▼
        State: worker_results = {
            "retrieval_worker": {...},
            "code_worker": {...},
            "analysis_worker": {...}
        }
                          │
                          ▼
        ┌───────────────────────────────────┐
        │   Supervisor Combine Node         │
        │  ┌─────────────────────────────┐  │
        │  │ 1. Read all worker results  │  │
        │  │ 2. Combine information      │  │
        │  │ 3. Generate final answer    │  │
        │  │ 4. Format response          │  │
        │  └─────────────────────────────┘  │
        └───────────────┬───────────────────┘
                        │
                        ▼
        State: combined_result = "Combined answer..."
        State: final_answer = "Final formatted answer..."
                        │
                        ▼
                ┌───────────────┐
                │      END      │
                └───────────────┘
```

### Supervisor Decision Tree

```
Question
    │
    ├─ Simple question?
    │   └─ Use: RetrievalWorker only
    │
    ├─ Code-related?
    │   └─ Use: RetrievalWorker + CodeWorker
    │
    ├─ Comparison question?
    │   └─ Use: RetrievalWorker + ComparisonWorker
    │
    ├─ Complex multi-domain?
    │   └─ Use: RetrievalWorker + AnalysisWorker + CodeWorker
    │
    └─ Unknown?
        └─ Use: All workers (default)
```

---

## State Flow Comparison

### Sequential Pattern State Flow

```
Initial
  │
  ├─ research_context: None
  ├─ analyzed_info: None
  └─ final_answer: ""
  │
  ▼ Research
  │
  ├─ research_context: [doc1, doc2, ...]
  └─ context: [doc1, doc2, ...]
  │
  ▼ Analysis
  │
  ├─ analyzed_info: "Structured..."
  └─ context: [doc1, doc2, ...]
  │
  ▼ Synthesis
  │
  └─ final_answer: "Complete answer..."
  │
  ▼ END
```

### Parallel Pattern State Flow

```
Initial
  │
  ├─ candidate_answers: None
  ├─ evaluation_scores: None
  └─ selected_answer: None
  │
  ▼ Parallel Execution
  │
  ├─ candidate_answers: {
  │     "structured_rag": "...",
  │     "agentic_rag": "...",
  │     "research_agent": "..."
  │   }
  │
  ▼ Evaluation
  │
  ├─ selected_answer: "..."
  ├─ selected_agent: "agentic_rag"
  └─ evaluation_scores: {...}
  │
  ▼ END
```

### Supervisor Pattern State Flow

```
Initial
  │
  ├─ supervisor_plan: None
  ├─ workers_used: None
  ├─ worker_results: None
  └─ combined_result: None
  │
  ▼ Supervisor Planning
  │
  ├─ supervisor_plan: "Use workers X, Y, Z"
  └─ workers_used: ["worker_x", "worker_y", "worker_z"]
  │
  ▼ Worker Execution
  │
  └─ worker_results: {
      "worker_x": {...},
      "worker_y": {...},
      "worker_z": {...}
    }
  │
  ▼ Combine
  │
  ├─ combined_result: "..."
  └─ final_answer: "..."
  │
  ▼ END
```

---

## Error Handling Flows

### Sequential Pattern Error Handling

```
Research Agent Error
    │
    ├─ Try alternative tool
    │   └─ Success → Continue
    │   └─ Fail → Return error
    │
Analysis Agent Error
    │
    ├─ Use raw research_context
    │   └─ Continue to Synthesis
    │
Synthesis Agent Error
    │
    └─ Return analyzed_info as answer
```

### Parallel Pattern Error Handling

```
Agent 1 Error
    │
    ├─ Continue with Agent 2, 3
    │   └─ Evaluator handles partial results
    │
All Agents Error
    │
    └─ Return error to user
```

### Supervisor Pattern Error Handling

```
Supervisor Error
    │
    └─ Use default workers
        └─ Continue execution
    │
Worker Error
    │
    ├─ Supervisor handles gracefully
    └─ Continue with other workers
```

---

## Performance Characteristics

### Sequential Pattern

```
Time: O(n) where n = number of agents
Memory: O(1) - sequential processing
Latency: Sum of all agent times
```

### Parallel Pattern

```
Time: O(1) - parallel execution
Memory: O(n) where n = number of agents
Latency: Max of all agent times
```

### Supervisor Pattern

```
Time: O(n) where n = number of workers
Memory: O(n) - parallel workers
Latency: Supervisor time + Max worker time
```

---

## Next Steps

1. Review all workflow diagrams
2. Understand state transitions
3. Review error handling
4. Approve for implementation

