# 🏗️ Multi-Agent System Architecture

## 📋 Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Agent Types & Roles](#agent-types--roles)
4. [Workflow Patterns](#workflow-patterns)
5. [State Management](#state-management)
6. [Communication Patterns](#communication-patterns)
7. [Implementation Phases](#implementation-phases)
8. [Sample Specifications](#sample-specifications)

---

## 🎯 Overview

### Goal
Build a multi-agent RAG system using LangGraph that extends our existing Structured and Agentic RAG implementations with collaborative agent workflows.

### Key Principles
- **Modular**: Each agent has a clear, single responsibility
- **Composable**: Agents can be combined in different patterns
- **Extensible**: Easy to add new agents or patterns
- **Observable**: Full tracing and logging for debugging
- **Reusable**: Leverage existing tools and infrastructure

---

## 🏛️ System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Multi-Agent Orchestrator                  │
│                    (LangGraph StateGraph)                    │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│   Pattern 1   │  │   Pattern 2   │  │   Pattern 3   │
│  Sequential   │  │   Parallel    │  │  Supervisor   │
│   Pipeline    │  │  Competitive  │  │   - Worker    │
└───────────────┘  └───────────────┘  └───────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│  Research     │  │  Structured   │  │  Supervisor   │
│  Agent        │  │  RAG Agent    │  │  Agent        │
├───────────────┤  ├───────────────┤  ├───────────────┤
│  Analysis     │  │  Agentic      │  │  Worker 1     │
│  Agent        │  │  RAG Agent    │  │  Worker 2     │
├───────────────┤  ├───────────────┤  │  Worker 3     │
│  Synthesis    │  │  Evaluator    │  │  ...          │
│  Agent        │  │  Agent        │  └───────────────┘
└───────────────┘  └───────────────┘
        │                   │
        └───────────────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
        ▼           ▼           ▼
┌───────────┐ ┌───────────┐ ┌───────────┐
│  Tools    │ │  Vector   │ │  Memory   │
│  Layer    │ │    DB     │ │  System   │
└───────────┘ └───────────┘ └───────────┘
```

### Component Layers

1. **Orchestration Layer** (LangGraph)
   - Manages agent workflows
   - Handles state transitions
   - Routes between agents

2. **Agent Layer**
   - Specialized agents (Research, Analysis, Synthesis, etc.)
   - Each agent has specific capabilities
   - Agents can call tools and other agents

3. **Tool Layer**
   - Existing tools (retrieve, keyword_search, metadata_search, summarize)
   - Shared across all agents
   - Extensible for new tools

4. **Data Layer**
   - Vector database (existing)
   - Memory system (existing)
   - Context storage

---

## 🤖 Agent Types & Roles

### 1. Research Agent
**Purpose**: Gather information from documents

**Responsibilities**:
- Retrieve relevant documents using semantic search
- Perform keyword searches for specific terms
- Search by metadata when needed
- Collect comprehensive information on the topic

**Tools Used**:
- `retrieve_tool` (primary)
- `keyword_search_tool`
- `metadata_search_tool`

**Output**: Raw context documents

---

### 2. Analysis Agent
**Purpose**: Analyze and structure gathered information

**Responsibilities**:
- Analyze retrieved documents
- Extract key points and insights
- Identify relationships and patterns
- Structure information logically
- Filter irrelevant content

**Tools Used**:
- `summarize_tool` (for long contexts)
- LLM for analysis

**Input**: Raw context from Research Agent
**Output**: Structured, analyzed information

---

### 3. Synthesis Agent
**Purpose**: Combine information into final answer

**Responsibilities**:
- Synthesize analyzed information
- Generate comprehensive answer
- Ensure coherence and completeness
- Format response appropriately

**Tools Used**:
- LLM for generation

**Input**: Analyzed information from Analysis Agent
**Output**: Final answer

---

### 4. Evaluator Agent
**Purpose**: Evaluate and compare multiple answers

**Responsibilities**:
- Compare answers from different agents
- Score answers on quality metrics
- Select best answer
- Provide reasoning for selection

**Tools Used**:
- LLM for evaluation

**Input**: Multiple candidate answers
**Output**: Selected best answer + reasoning

---

### 5. Supervisor Agent
**Purpose**: Coordinate and delegate tasks to workers

**Responsibilities**:
- Analyze incoming question
- Determine which workers are needed
- Delegate tasks to appropriate workers
- Combine worker results
- Make final decision

**Tools Used**:
- LLM for decision making

**Input**: User question
**Output**: Coordinated final answer

---

### 6. Worker Agents (Specialized)
**Purpose**: Perform specific tasks as delegated by supervisor

**Types**:
- **Retrieval Worker**: Specialized document retrieval
- **Code Worker**: Code-related queries
- **Concept Worker**: Conceptual explanations
- **Comparison Worker**: Compare multiple topics

**Responsibilities**:
- Execute assigned task
- Return results to supervisor

---

## 🔄 Workflow Patterns

### Pattern 1: Sequential Pipeline

**Flow**:
```
User Question
    ↓
[Research Agent] → Gathers information
    ↓
[Analysis Agent] → Analyzes and structures
    ↓
[Synthesis Agent] → Creates final answer
    ↓
Final Answer
```

**State Transitions**:
```
Initial State
    → research_node (Research Agent)
    → analysis_node (Analysis Agent)
    → synthesis_node (Synthesis Agent)
    → END
```

**Use Cases**:
- Complex questions requiring multiple steps
- Questions needing deep analysis
- Research-intensive queries

**Example**: "Compare circuit breakers and load balancing, explain their differences and use cases"

---

### Pattern 2: Parallel Competitive

**Flow**:
```
User Question
    ↓
    ┌─────────────┬─────────────┬─────────────┐
    ↓             ↓             ↓             ↓
[Structured]  [Agentic]    [Research]    [Keyword]
   RAG          RAG         Agent         Search
    ↓             ↓             ↓             ↓
    └─────────────┴─────────────┴─────────────┘
                    ↓
            [Evaluator Agent]
            Selects best answer
                    ↓
            Final Answer
```

**State Transitions**:
```
Initial State
    → parallel_branch (all agents run simultaneously)
    → evaluator_node (Evaluator Agent)
    → END
```

**Use Cases**:
- When you want to try multiple approaches
- Comparing different RAG strategies
- Ensuring best possible answer

**Example**: "What is a circuit breaker?" (try all approaches, pick best)

---

### Pattern 3: Supervisor-Worker

**Flow**:
```
User Question
    ↓
[Supervisor Agent]
Analyzes question, decides workers
    ↓
    ┌─────────────┬─────────────┬─────────────┐
    ↓             ↓             ↓             ↓
[Worker 1]   [Worker 2]   [Worker 3]   [Worker 4]
(Retrieval)  (Analysis)   (Code)       (Comparison)
    ↓             ↓             ↓             ↓
    └─────────────┴─────────────┴─────────────┘
                    ↓
            [Supervisor Agent]
            Combines results
                    ↓
            Final Answer
```

**State Transitions**:
```
Initial State
    → supervisor_node (Supervisor Agent)
    → delegate_to_workers (parallel workers)
    → combine_results (Supervisor Agent)
    → END
```

**Use Cases**:
- Complex multi-domain questions
- Questions requiring different expertise
- Dynamic task delegation

**Example**: "Explain how to implement circuit breaker pattern in microservices with code examples"

---

## 📦 State Management

### MultiAgentState (TypedDict)

```python
class MultiAgentState(TypedDict):
    # Core fields
    session_id: str
    question: str
    final_answer: str
    
    # Pattern-specific fields
    pattern: Literal["sequential", "parallel", "supervisor"]
    
    # Sequential pattern fields
    research_context: List[str]  # Research Agent output
    analyzed_info: str  # Analysis Agent output
    
    # Parallel pattern fields
    candidate_answers: Dict[str, str]  # {agent_name: answer}
    evaluation_scores: Dict[str, float]  # {agent_name: score}
    selected_answer: Optional[str]  # Evaluator's choice
    
    # Supervisor pattern fields
    supervisor_plan: Optional[str]  # Supervisor's task plan
    worker_results: Dict[str, Any]  # {worker_name: result}
    combined_result: Optional[str]  # Supervisor's combined result
    
    # Common fields
    context: List[str]  # Accumulated context
    metadata: Dict[str, Any]  # Additional metadata
    error: Optional[str]  # Error message if any
    iteration_count: int  # Track iterations
```

### State Flow Example (Sequential)

```
Initial State:
{
    "question": "What is a circuit breaker?",
    "pattern": "sequential",
    "research_context": [],
    "analyzed_info": "",
    "final_answer": "",
    "context": [],
    "iteration_count": 0
}

After Research Agent:
{
    "research_context": ["doc1", "doc2", "doc3"],
    "context": ["doc1", "doc2", "doc3"]
}

After Analysis Agent:
{
    "analyzed_info": "Structured analysis of circuit breaker...",
    "context": ["doc1", "doc2", "doc3"]
}

After Synthesis Agent:
{
    "final_answer": "A circuit breaker is...",
    "context": ["doc1", "doc2", "doc3"]
}
```

---

## 💬 Communication Patterns

### 1. Direct State Passing (Sequential)
- Agents pass state directly through LangGraph
- Each agent reads from and writes to shared state
- Simple, synchronous communication

### 2. Parallel Execution (Parallel)
- Multiple agents execute simultaneously
- Each agent writes to separate state keys
- Evaluator reads all results and selects best

### 3. Delegation (Supervisor-Worker)
- Supervisor writes task assignments to state
- Workers read assignments and write results
- Supervisor reads all results and combines

### 4. Tool Sharing
- All agents share the same tool layer
- Tools are stateless and reusable
- No direct agent-to-agent communication needed

---

## 🚀 Implementation Phases

### Phase 1: Foundation (Week 1)
**Goal**: Set up infrastructure

- [ ] Create multi-agent directory structure
- [ ] Define MultiAgentState
- [ ] Create base agent classes
- [ ] Set up LangGraph orchestration
- [ ] Integrate with existing tools

**Deliverables**:
- Basic multi-agent framework
- Working state management
- Tool integration

---

### Phase 2: Sequential Pattern (Week 1-2)
**Goal**: Implement sequential pipeline

- [ ] Research Agent implementation
- [ ] Analysis Agent implementation
- [ ] Synthesis Agent implementation
- [ ] Sequential workflow graph
- [ ] Testing and validation

**Deliverables**:
- Working sequential multi-agent system
- Test cases
- Documentation

---

### Phase 3: Parallel Pattern (Week 2)
**Goal**: Implement parallel competitive pattern

- [ ] Parallel execution framework
- [ ] Evaluator Agent implementation
- [ ] Parallel workflow graph
- [ ] Answer comparison logic
- [ ] Testing and validation

**Deliverables**:
- Working parallel multi-agent system
- Evaluation metrics
- Comparison reports

---

### Phase 4: Supervisor-Worker Pattern (Week 3)
**Goal**: Implement supervisor-worker pattern

- [ ] Supervisor Agent implementation
- [ ] Worker Agent implementations
- [ ] Task delegation logic
- [ ] Result combination logic
- [ ] Testing and validation

**Deliverables**:
- Working supervisor-worker system
- Dynamic task delegation
- Worker specialization

---

### Phase 5: Integration & Polish (Week 3-4)
**Goal**: Integrate with existing system

- [ ] FastAPI router for multi-agent
- [ ] UI integration
- [ ] Error handling
- [ ] Logging and tracing
- [ ] Performance optimization
- [ ] Documentation

**Deliverables**:
- Production-ready multi-agent system
- API endpoints
- UI support
- Complete documentation

---

## 📝 Sample Specifications

See [SPECIFICATIONS.md](./SPECIFICATIONS.md) for detailed specifications.

---

## 🔍 Next Steps

1. Review this architecture document
2. Review sample specifications
3. Provide feedback on:
   - Agent roles and responsibilities
   - Workflow patterns
   - State management
   - Implementation phases
4. Approve for development

---

## 📚 Related Documents

- [SPECIFICATIONS.md](./SPECIFICATIONS.md) - Detailed specifications
- [WORKFLOW_DIAGRAMS.md](./WORKFLOW_DIAGRAMS.md) - Visual workflow diagrams
- [API_DESIGN.md](./API_DESIGN.md) - API endpoint design

