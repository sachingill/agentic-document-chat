# Search Methods: Vector Search, Keyword Search, and BM25

## Current State

### ❌ BM25: **NOT USED**
- No BM25 implementation found in the codebase
- No `rank_bm25`, `BM25`, or similar imports

### ✅ Vector Search: **PRIMARY METHOD**
- Semantic search using embeddings
- Used as the main retrieval mechanism

### ✅ Keyword Search: **AVAILABLE BUT LIMITED**
- Simple string matching (not BM25)
- Used as a fallback/complementary method

---

## 1. Vector Search (Semantic Search)

### Implementation

**Location:** `app/models/embeddings.py`, `app/agents/tools.py`

**How it works:**
- Uses **HuggingFace embeddings** (`sentence-transformers/all-MiniLM-L6-v2`)
- Stores embeddings in **ChromaDB** vector database
- Retrieves top-k most similar chunks by cosine similarity

**Code:**
```python
def retrieve_tool(query: str, k: int = 10):
    """
    Retrieves top relevant chunks from vector DB using semantic similarity.
    """
    retriever = get_retriever(k=k)
    docs = retriever.invoke(query)  # Semantic search
    return {"results": [...], "documents": [...], "count": len(docs)}
```

### Where It's Used

1. **Structured RAG** (`app/agents/doc_agent.py`):
   ```python
   # Primary retrieval method
   res = retrieve_tool(question)  # Vector search
   docs = res.get("documents")
   ```

2. **Agentic RAG** (`app/agents/agentic_flow.py`):
   ```python
   # Default tool selection
   result = retrieve_tool(question, k=5)  # Vector search
   ```

3. **Multi-Agent RAG** (`multiagent/app/agents/research_agent.py`):
   ```python
   # Primary semantic search
   result = retrieve_tool(question)
   semantic_docs = result.get("results", [])
   ```

4. **RCA Agent** (`app/agents/rca_tools.py`):
   ```python
   # Error pattern search uses vector search
   result = retrieve_tool(query, k=k)
   ```

### Advantages
- ✅ **Semantic Understanding**: Finds conceptually similar content
- ✅ **Handles Synonyms**: "authentication" matches "login", "auth", etc.
- ✅ **Context-Aware**: Understands meaning, not just keywords

### Limitations
- ⚠️ **Exact Match Misses**: May miss exact keyword matches
- ⚠️ **Domain-Specific Terms**: May struggle with technical terms
- ⚠️ **No Ranking**: Pure similarity, no TF-IDF weighting

---

## 2. Keyword Search (Simple String Matching)

### Implementation

**Location:** `app/agents/tools.py` (function: `keyword_search_tool`)

**How it works:**
- **Simple substring matching** (NOT BM25)
- Searches all documents for keyword occurrence
- Case-insensitive matching

**Code:**
```python
def keyword_search_tool(keyword: str):
    """
    Performs literal keyword search over stored documents.
    Simple string matching - NOT BM25.
    """
    retriever = get_retriever()
    all_docs = retriever.vectorstore._collection.get(include=["documents"])
    
    matches = [
        doc
        for doc in all_docs["documents"]
        if keyword.lower() in doc.lower()  # Simple substring match
    ]
    
    return {"keyword": keyword, "matches": matches, "count": len(matches)}
```

### Where It's Used

1. **Multi-Agent RAG** (`multiagent/app/agents/research_agent.py`):
   ```python
   # Used when strategy indicates keyword search needed
   if strategy.get("needs_keyword"):
       keywords = _extract_keywords(question)
       for keyword in keywords[:3]:
           result = keyword_search_tool(keyword)  # Keyword search
           matches.extend(result.get("matches", []))
   ```

2. **Agentic RAG** (`agentic/app/agents/agentic_agent.py`):
   ```python
   # Used when agent selects keyword_search_tool
   if tool_name == "keyword_search_tool":
       keywords = _extract_keywords_llm(question)
       for keyword in keywords:
           result = keyword_search_tool(keyword)  # Keyword search
   ```

### Advantages
- ✅ **Exact Matches**: Finds exact keyword occurrences
- ✅ **Fast**: Simple string matching
- ✅ **Complementary**: Works alongside vector search

### Limitations
- ⚠️ **No Ranking**: All matches treated equally
- ⚠️ **No TF-IDF**: Doesn't weight by term frequency
- ⚠️ **No BM25**: Not using BM25 algorithm
- ⚠️ **Substring Matching**: May return false positives

---

## 3. BM25: **NOT IMPLEMENTED**

### Current Status
- ❌ **No BM25 library** (e.g., `rank_bm25`, `pyserini`)
- ❌ **No BM25 implementation** in codebase
- ❌ **No hybrid search** combining BM25 + vector search

### What BM25 Would Provide

**BM25 (Best Matching 25)** is a ranking function that:
- Scores documents based on term frequency (TF)
- Uses inverse document frequency (IDF) for weighting
- Handles exact keyword matches better than pure vector search
- Often used in **hybrid search** (BM25 + vector search)

**Benefits if added:**
- ✅ Better exact keyword matching
- ✅ Handles technical terms better
- ✅ Can combine with vector search for hybrid retrieval
- ✅ Proven effectiveness in information retrieval

---

## Search Strategy by System

### Structured RAG
```
Query → Vector Search (k=10) → Rerank → Top 3
```
- **Primary**: Vector search only
- **No keyword search**
- **No BM25**

### Agentic RAG
```
Query → Tool Selection → {
    "retrieve_tool": Vector Search
    "keyword_search_tool": Keyword Search (simple)
    "metadata_search_tool": Metadata Filtering
}
```
- **Primary**: Vector search
- **Fallback**: Keyword search (when agent selects it)
- **No BM25**

### Multi-Agent RAG
```
Query → Strategy Selection → {
    Semantic Search: Vector Search
    Keyword Search: Simple String Matching
    Metadata Search: Metadata Filtering
}
```
- **Primary**: Vector search
- **Complementary**: Keyword search (when strategy indicates)
- **No BM25**

### RCA Agent
```
Error Query → Vector Search → Pattern Matching
```
- **Primary**: Vector search
- **No keyword search**
- **No BM25**

---

## Comparison: Current vs BM25

| Feature | Current Keyword Search | BM25 | Vector Search |
|---------|----------------------|------|---------------|
| **Algorithm** | Simple substring | TF-IDF based | Embedding similarity |
| **Ranking** | ❌ None | ✅ Yes (BM25 score) | ✅ Yes (cosine similarity) |
| **Exact Matches** | ✅ Yes | ✅ Yes | ⚠️ Sometimes |
| **Semantic Understanding** | ❌ No | ❌ No | ✅ Yes |
| **Term Frequency** | ❌ Ignored | ✅ Used | ❌ Ignored |
| **Inverse Doc Frequency** | ❌ Ignored | ✅ Used | ❌ Ignored |
| **Performance** | Fast | Medium | Medium |
| **Use Case** | Exact keywords | Keyword + ranking | Semantic similarity |

---

## Recommendation: Add BM25 for Hybrid Search

### Why Add BM25?

1. **Better Exact Matching**: BM25 excels at exact keyword matches
2. **Hybrid Search**: Combine BM25 + Vector Search for best of both worlds
3. **Technical Terms**: Better handling of domain-specific terminology
4. **Proven Effectiveness**: BM25 is a proven IR algorithm

### Implementation Approach

**Option 1: Pure BM25 Replacement**
```python
from rank_bm25 import BM25Okapi

def bm25_search_tool(query: str, k: int = 10):
    """
    BM25-based keyword search with ranking.
    """
    # Tokenize documents
    tokenized_docs = [doc.split() for doc in all_documents]
    bm25 = BM25Okapi(tokenized_docs)
    
    # Search
    tokenized_query = query.split()
    scores = bm25.get_scores(tokenized_query)
    
    # Return top-k
    top_indices = np.argsort(scores)[::-1][:k]
    return top_results
```

**Option 2: Hybrid Search (Recommended)**
```python
def hybrid_search(query: str, k: int = 10):
    """
    Combine BM25 and vector search for best results.
    """
    # BM25 search
    bm25_results = bm25_search_tool(query, k=k*2)
    
    # Vector search
    vector_results = retrieve_tool(query, k=k*2)
    
    # Combine and rerank
    combined = merge_results(bm25_results, vector_results)
    reranked = await rerank(query, combined, top_k=k)
    
    return reranked
```

### Where to Use BM25

1. **RCA Agent**: Better error pattern matching
2. **Multi-Agent RAG**: When keyword strategy is selected
3. **Hybrid Search**: Combine with vector search for all queries

---

## Current Search Flow Summary

### Structured RAG
```
Query → Vector Search (k=10) → Rerank (top 3) → Answer
```

### Agentic RAG
```
Query → Tool Selection → {
    Vector Search (default)
    OR Keyword Search (simple)
    OR Metadata Search
} → Answer
```

### Multi-Agent RAG
```
Query → Strategy → {
    Vector Search (semantic)
    + Keyword Search (simple, if needed)
    + Metadata Search (if needed)
} → Merge → Answer
```

---

## Summary

| Search Method | Status | Where Used | Algorithm |
|--------------|--------|------------|-----------|
| **Vector Search** | ✅ Primary | All systems | Embedding similarity |
| **Keyword Search** | ✅ Available | Multi-Agent, Agentic | Simple substring |
| **BM25** | ❌ Not Used | None | N/A |

**Current Approach:**
- **Primary**: Vector search (semantic)
- **Fallback**: Simple keyword matching (not BM25)
- **Missing**: BM25 ranking algorithm

**Recommendation:**
- Consider adding BM25 for better keyword matching
- Implement hybrid search (BM25 + Vector) for improved retrieval
- Especially useful for technical/domain-specific queries

