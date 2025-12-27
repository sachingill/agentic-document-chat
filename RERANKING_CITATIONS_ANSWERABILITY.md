# Reranking, Citation Enforcement, and Answerability Checks

## Overview

This document explains how the RAG system handles three critical quality mechanisms:
1. **Reranking** - Improving retrieval relevance
2. **Citation Enforcement** - Ensuring answers are grounded in sources
3. **Answerability Checks** - Verifying answers are supported by context

---

## 1. Reranking

### Purpose
Re-rank retrieved chunks by relevance to the query using an LLM, improving retrieval quality.

### Implementation

**Location:** `app/agents/reranker.py`

**How it works:**
1. **Initial Retrieval**: Vector DB returns top-k chunks (default k=10)
2. **LLM Scoring**: Each chunk is scored 0-1 for relevance to the query
3. **Parallel Processing**: All chunks scored concurrently for performance
4. **Top-K Selection**: Returns top-k most relevant chunks (default top_k=3)

**Code:**
```python
async def rerank(question: str, docs: List[Any], top_k: int = 3) -> List[RerankDoc]:
    """
    Re-ranks retrieved chunks based on relevance using an LLM.
    Returns top_k chunks (best-first), preserving metadata.
    """
    # Score each chunk: 0.0 to 1.0 relevance score
    # Sort by score (descending)
    # Return top_k chunks
```

**Scoring Prompt:**
```
You are a relevance scorer. Evaluate how relevant this document chunk is to the user question.
Score strictly between 0 and 1.

Question: {question}
Document Chunk: {chunk}

Respond with only the numeric score.
```

### Where It's Used

1. **Structured RAG** (`app/agents/doc_agent.py`):
   ```python
   # After vector retrieval
   docs = retriever.invoke(query)  # Get top 10
   ranked = await rerank(question, docs, top_k=3)  # Rerank to top 3
   ```

2. **Multi-Query Retrieval** (`app/agents/doc_agent.py`):
   ```python
   # After merging results from multiple queries
   merged_docs = merge_results(query1_results, query2_results, ...)
   ranked = await rerank(question, merged_docs, top_k=5)  # Rerank merged results
   ```

### Configuration

- **LLM**: `fast_llm(temperature=0.0)` - Deterministic scoring
- **Default top_k**: 3 chunks (configurable)
- **Initial retrieval**: k=10 (gives reranker more candidates)

### Benefits

- ✅ **Better Relevance**: LLM understands semantic relevance better than pure embedding similarity
- ✅ **Noise Reduction**: Filters out less relevant chunks
- ✅ **Performance**: Parallel scoring for speed

### Limitations

- ⚠️ **Cost**: Requires LLM calls (one per chunk)
- ⚠️ **Latency**: Adds ~100-500ms depending on chunk count
- ⚠️ **Determinism**: LLM scoring may vary slightly

---

## 2. Citation Enforcement

### Purpose
Ensure answers are grounded in retrieved documents and provide traceable citations.

### Implementation

**Location:** `app/agents/doc_agent.py`

**How it works:**

1. **Citation Collection**: During retrieval, collect chunks with metadata
2. **Citation Attachment**: Attach citations to final answer
3. **Metadata Preservation**: Include chunk_id, doc_id, start_index for traceability

**Code Flow:**
```python
# 1. Retrieve chunks with metadata
docs = retriever.invoke(query)
ranked = await rerank(question, docs, top_k=3)

# 2. Generate answer using ranked chunks
answer = llm.generate(context=ranked_chunks)

# 3. Attach citations from chunks used
citations = [
    {
        "text": chunk.get("text", ""),
        "metadata": chunk.get("metadata", {}),
        "chunk_id": chunk.metadata.get("chunk_id"),
        "doc_id": chunk.metadata.get("doc_id"),
        "start_index": chunk.metadata.get("start_index")
    }
    for chunk in ranked_chunks
]
```

### Citation Format

```python
{
    "text": "Chunk text content...",
    "metadata": {
        "chunk_id": "doc_0::chunk_2",
        "doc_id": "doc_0",
        "chunk_index": 2,
        "start_index": 450,
        "filename": "document.pdf",
        "source": "api-server"
    }
}
```

### Where Citations Are Used

1. **Structured RAG** (`/agent/chat`):
   - Returns citations with every answer
   - UI displays citations below answers

2. **Agentic RAG** (`/agentic/chat`):
   - Collects citations from all tool calls
   - Deduplicates by chunk_id
   - Returns top 5 citations

3. **Multi-Agent RAG** (`/multiagent/chat`):
   - Citations from research agent
   - Citations from synthesis agent
   - Merged and deduplicated

### Citation Deduplication

**Location:** `app/agents/doc_agent.py`, `app/agents/agentic_flow.py`

```python
# Deduplicate by chunk_id (if present) or by text prefix
seen = set()
deduped = []
for c in citations:
    key = c.get("metadata", {}).get("chunk_id") or c.get("text", "")[:120]
    if key not in seen:
        seen.add(key)
        deduped.append(c)
```

### Enforcement Mechanisms

1. **Metadata Tracking**: Every chunk has `chunk_id`, `doc_id`, `start_index`
2. **Source Traceability**: Citations include filename, source, timestamp
3. **UI Display**: Citations shown in Streamlit UI for verification

### Benefits

- ✅ **Transparency**: Users can verify sources
- ✅ **Traceability**: Can locate exact document positions
- ✅ **Trust**: Builds confidence in answers

### Limitations

- ⚠️ **No Automatic Verification**: Citations aren't automatically verified for accuracy
- ⚠️ **Manual Review**: Users must manually check if citations match answers

---

## 3. Answerability Checks

### Purpose
Verify that generated answers are actually supported by the provided context, preventing hallucinations.

### Implementation

**Location:** `app/agents/inference_utils.py`

**Function:** `verify_supported(question, context, answer)`

**How it works:**

1. **LLM Verifier**: Uses a fast LLM to check if answer is supported
2. **Strict Checking**: Flags answers with unsupported claims
3. **Fallback to IDK**: If not supported, returns "I don't know"

**Code:**
```python
def verify_supported(*, question: str, context: str, answer: str) -> Dict[str, Any]:
    """
    Lightweight verifier: checks whether the answer is supported by provided context.
    Returns dict: {supported: bool, reason: str}
    """
    prompt = f"""You are a strict verifier.

Question: {question}
Context: {context}
Answer: {answer}

Decide if the Answer is fully supported by the Context.
If the answer includes claims not in the context, mark supported=false.

Return JSON only:
{{"supported": true|false, "reason": "<short>"}}
"""
    # LLM evaluates and returns verdict
    return {"supported": bool, "reason": str}
```

### Where It's Used

1. **Structured RAG** (`app/agents/doc_agent.py`):
   ```python
   # After generating answer
   if cfg.verify_answer and response != IDK_SENTINEL:
       verdict = verify_supported(question, context, response)
       if not verdict["supported"]:
           response = IDK_SENTINEL  # Reject unsupported answer
   ```

2. **Agentic RAG** (`app/agents/agentic_flow.py`):
   ```python
   # After generating final answer
   if cfg.verify_answer and answer != IDK_SENTINEL:
       verdict = verify_supported(question, context, answer)
       if not verdict["supported"]:
           answer = IDK_SENTINEL
   ```

3. **Multi-Agent RAG** (`multiagent/app/agents/synthesis_agent.py`):
   ```python
   # After synthesis agent generates answer
   if cfg.verify_answer:
       verdict = verify_supported(question, context, final_answer)
       if not verdict["supported"]:
           final_answer = IDK_SENTINEL
   ```

### Configuration by Inference Mode

**Location:** `app/agents/inference_modes.py`

| Mode | `verify_answer` | Behavior |
|------|-----------------|----------|
| **Low** | `False` | No verification (fastest, less strict) |
| **Balanced** | `True` | Verifies answers (default) |
| **High** | `True` | Verifies + requires min_chunks (strictest) |

### Evidence Gates

**Additional Answerability Check:**

Before even generating an answer, check if there's enough evidence:

```python
# Evidence gate (high-strictness)
if mode == "high" and len(context_chunks) < cfg.min_chunks:
    response = IDK_SENTINEL  # Don't even try to answer
    return response
```

**Min Chunks by Mode:**
- **Low**: 1 chunk minimum
- **Balanced**: 2 chunks minimum
- **High**: 3 chunks minimum

### Verifier Prompt Strategy

The verifier uses a **strict** approach:
- ✅ **Supported**: Answer facts are all in context
- ❌ **Not Supported**: Answer contains claims not in context
- 🔍 **Reasoning**: Provides short explanation

**Example:**
```
Question: "What is authentication?"
Context: "Authentication verifies user identity..."
Answer: "Authentication verifies user identity and uses OAuth2"

Verdict: {"supported": false, "reason": "OAuth2 not mentioned in context"}
```

### Benefits

- ✅ **Prevents Hallucinations**: Catches unsupported claims
- ✅ **Improves Accuracy**: Only returns verified answers
- ✅ **Configurable**: Can disable for speed (low mode)

### Limitations

- ⚠️ **LLM Dependency**: Requires LLM call (adds latency)
- ⚠️ **False Negatives**: May reject valid answers if verifier is too strict
- ⚠️ **False Positives**: May accept answers if verifier misses unsupported claims
- ⚠️ **Conservative Fallback**: If verifier fails to parse, defaults to "supported"

---

## Integration Flow

### Complete Flow with All Three Mechanisms

```
1. Query Input
   ↓
2. Vector Retrieval (k=10)
   ↓
3. RERANKING ← Improves relevance
   ↓
4. Top-k Chunks Selected (k=3)
   ↓
5. Answer Generation
   ↓
6. ANSWERABILITY CHECK ← Verifies support
   ↓
7. If supported → Return answer + citations
   If not supported → Return "I don't know"
   ↓
8. CITATION ENFORCEMENT ← Attach sources
   ↓
9. Final Response with Citations
```

### Code Example (Structured RAG)

```python
# 1. Retrieve
docs = retriever.invoke(query, k=10)

# 2. Rerank
ranked = await rerank(question, docs, top_k=3)

# 3. Generate
context = "\n\n".join([chunk["text"] for chunk in ranked])
answer = llm.generate(context=context, question=question)

# 4. Answerability Check
if cfg.verify_answer:
    verdict = verify_supported(question, context, answer)
    if not verdict["supported"]:
        answer = "I don't know based on the documents."

# 5. Citation Enforcement
citations = [
    {"text": chunk["text"], "metadata": chunk["metadata"]}
    for chunk in ranked
]

return {"answer": answer, "citations": citations}
```

---

## Configuration

### Inference Modes

**Location:** `app/agents/inference_modes.py`

```python
INFERENCE_CONFIGS = {
    "low": {
        "min_chunks": 1,
        "verify_answer": False,  # No answerability check
        "second_pass_k": 5
    },
    "balanced": {
        "min_chunks": 2,
        "verify_answer": True,   # Answerability check enabled
        "second_pass_k": 8
    },
    "high": {
        "min_chunks": 3,
        "verify_answer": True,   # Answerability check enabled
        "second_pass_k": 10
    }
}
```

### Usage

```python
# Via API
POST /agent/chat
{
    "question": "What is authentication?",
    "inference_mode": "balanced"  # or "low", "high"
}
```

---

## Performance Impact

| Mechanism | Latency Added | Cost Impact |
|-----------|---------------|-------------|
| **Reranking** | ~200-500ms | Medium (LLM calls per chunk) |
| **Answerability Check** | ~100-300ms | Low (single LLM call) |
| **Citation Enforcement** | ~0-50ms | None (just metadata) |

**Total Impact:**
- **Low mode**: ~200ms (reranking only)
- **Balanced mode**: ~400ms (reranking + answerability)
- **High mode**: ~500ms (reranking + answerability + evidence gates)

---

## Best Practices

### When to Use Each Mechanism

1. **Reranking**: Always use (improves quality significantly)
2. **Answerability Check**: Use in production (balanced/high modes)
3. **Citation Enforcement**: Always use (builds trust)

### Tuning Recommendations

- **For Speed**: Use "low" mode, reduce rerank top_k to 2
- **For Quality**: Use "high" mode, increase rerank top_k to 5
- **For Balance**: Use "balanced" mode (default)

---

## Monitoring

Track these metrics:
- **Reranking**: Average score improvement, top-k selection rate
- **Answerability**: Rejection rate, false positive/negative rate
- **Citations**: Citation accuracy, citation coverage

---

## Future Improvements

1. **Better Reranking**: Use cross-encoders for more accurate scoring
2. **Citation Verification**: Automatically verify citations match answers
3. **Answerability**: Multi-step verification with claim extraction
4. **Confidence Scores**: Add confidence scores to answers

