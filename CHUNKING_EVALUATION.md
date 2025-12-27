# Chunking Strategy Evaluation Guide

## Overview

This guide explains how to evaluate the four key metrics for chunking effectiveness:
1. **Retrieval Precision**
2. **Context Completeness**
3. **Boundary Issues**
4. **Citation Accuracy**

---

## 1. Retrieval Precision

### What It Measures
**Are retrieved chunks relevant to the query?**

### How to Evaluate

#### Method A: Manual Evaluation (Gold Standard)
1. **Create Test Queries**
   - 10-20 diverse questions covering different topics
   - Mix of simple and complex queries
   - Include edge cases

2. **Retrieve Chunks**
   - Run each query through your RAG system
   - Collect top-k retrieved chunks (k=3-5)

3. **Rate Relevance**
   - For each chunk, rate: **Relevant (1)** or **Not Relevant (0)**
   - Calculate: `Precision = Relevant Chunks / Total Retrieved Chunks`

**Example:**
```
Query: "What is the authentication flow?"
Retrieved chunks: 5
Relevant chunks: 4
Precision = 4/5 = 0.80 (80%)
```

#### Method B: Automated Evaluation (LLM-Based)
Use an LLM to judge relevance:

```python
def evaluate_retrieval_precision(query: str, retrieved_chunks: List[str]) -> float:
    """
    Use LLM to evaluate if retrieved chunks are relevant to query.
    Returns precision score (0.0 to 1.0).
    """
    prompt = f"""
    Evaluate if these retrieved chunks are relevant to the query.
    
    Query: {query}
    
    Chunks:
    {chr(10).join([f"{i+1}. {chunk[:200]}..." for i, chunk in enumerate(retrieved_chunks)])}
    
    For each chunk, respond with:
    - "RELEVANT" if the chunk contains information relevant to the query
    - "NOT_RELEVANT" if the chunk is not relevant
    
    Format: One line per chunk, numbered 1-N.
    """
    
    # Use LLM to evaluate
    # Count RELEVANT responses / total chunks
    # Return precision score
```

#### Method C: Semantic Similarity
Compare query embedding with chunk embeddings:

```python
from sentence_transformers import SentenceTransformer

def semantic_precision(query: str, chunks: List[str], threshold=0.7):
    """
    Calculate precision based on semantic similarity.
    Chunks with similarity > threshold are considered relevant.
    """
    model = SentenceTransformer('all-MiniLM-L6-v2')
    query_embedding = model.encode(query)
    chunk_embeddings = model.encode(chunks)
    
    similarities = cosine_similarity([query_embedding], chunk_embeddings)[0]
    relevant = sum(1 for s in similarities if s > threshold)
    
    return relevant / len(chunks)
```

### Target Metrics
- **Good:** Precision > 0.70 (70% of retrieved chunks are relevant)
- **Excellent:** Precision > 0.85 (85% of retrieved chunks are relevant)

---

## 2. Context Completeness

### What It Measures
**Do chunks contain enough information to answer the question fully?**

### How to Evaluate

#### Method A: Answer Completeness Check
1. **Create Questions with Known Answers**
   - Questions that require specific information
   - Answers should be verifiable from documents

2. **Retrieve Chunks and Generate Answer**
   - Get top-k chunks for each question
   - Generate answer using RAG system

3. **Check Answer Completeness**
   - Does the answer contain all required information?
   - Is any critical information missing?

**Example:**
```
Question: "What are the three main authentication methods?"
Expected: ["OAuth2", "JWT", "API Key"]
Retrieved chunks: Only mention OAuth2 and JWT
Completeness: 2/3 = 0.67 (67% - Missing API Key)
```

#### Method B: Information Extraction Test
```python
def evaluate_completeness(question: str, answer: str, expected_entities: List[str]) -> float:
    """
    Check if answer contains all expected entities/information.
    """
    found_entities = []
    for entity in expected_entities:
        if entity.lower() in answer.lower():
            found_entities.append(entity)
    
    completeness = len(found_entities) / len(expected_entities)
    return completeness
```

#### Method C: Chunk Coverage Analysis
```python
def analyze_chunk_coverage(query: str, chunks: List[str], answer: str):
    """
    Check if answer can be derived from retrieved chunks.
    """
    # Extract key facts from answer
    # Check if each fact appears in at least one chunk
    # Calculate coverage percentage
```

### Target Metrics
- **Good:** Completeness > 0.75 (75% of required info present)
- **Excellent:** Completeness > 0.90 (90% of required info present)

---

## 3. Boundary Issues

### What It Measures
**Are related concepts split across multiple chunks?**

### How to Evaluate

#### Method A: Concept Coherence Test
1. **Identify Multi-Chunk Concepts**
   - Find concepts that span multiple chunks
   - Check if splitting breaks meaning

2. **Manual Review**
   - Review chunk boundaries in sample documents
   - Flag cases where concepts are fragmented

**Example:**
```
Document: "The authentication flow consists of three steps: 
1. User submits credentials
2. Server validates credentials  
3. Server issues token"

Chunk 1: "The authentication flow consists of three steps: 1. User submits"
Chunk 2: "credentials 2. Server validates credentials 3. Server issues token"

Issue: Step 1 is split across chunks (boundary problem)
```

#### Method B: Dependency Analysis
```python
def check_boundary_issues(chunks: List[str]):
    """
    Detect if related concepts are split across chunks.
    """
    issues = []
    
    for i in range(len(chunks) - 1):
        chunk1_end = chunks[i][-100:]  # Last 100 chars
        chunk2_start = chunks[i+1][:100]  # First 100 chars
        
        # Check for incomplete sentences
        if not chunk1_end.rstrip().endswith(('.', '!', '?', ':')):
            issues.append(f"Chunk {i} ends mid-sentence")
        
        # Check for split lists/enumerations
        if re.search(r'\d+\.\s*$', chunk1_end) and not chunk2_start[0].isdigit():
            issues.append(f"Chunk {i} splits enumeration")
    
    return issues
```

#### Method C: Semantic Coherence
```python
def semantic_coherence(chunks: List[str]):
    """
    Measure semantic similarity between adjacent chunks.
    Low similarity may indicate boundary issues.
    """
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    coherence_scores = []
    for i in range(len(chunks) - 1):
        emb1 = model.encode(chunks[i])
        emb2 = model.encode(chunks[i+1])
        similarity = cosine_similarity([emb1], [emb2])[0][0]
        coherence_scores.append(similarity)
    
    avg_coherence = sum(coherence_scores) / len(coherence_scores)
    return avg_coherence
```

### Target Metrics
- **Good:** < 10% of chunks have boundary issues
- **Excellent:** < 5% of chunks have boundary issues

---

## 4. Citation Accuracy

### What It Measures
**Can citations point to exact locations in source documents?**

### How to Evaluate

#### Method A: Citation Verification
1. **Generate Answers with Citations**
   - Run queries through RAG system
   - Collect citations (chunk IDs, document names, positions)

2. **Verify Citations**
   - Check if cited chunks actually contain the information
   - Verify document names are correct
   - Check if start_index positions are accurate

**Example:**
```
Answer: "Authentication uses OAuth2"
Citation: doc_5::chunk_2, start_index: 450

Verification:
- Check doc_5, chunk_2
- Verify "OAuth2" appears at position 450
- Result: ✅ Accurate or ❌ Inaccurate
```

#### Method B: Automated Citation Check
```python
def verify_citation(citation: dict, answer: str, documents: dict):
    """
    Verify if citation points to correct location.
    """
    doc_id = citation.get("doc_id")
    chunk_id = citation.get("chunk_id")
    start_index = citation.get("start_index")
    
    # Get the actual chunk
    chunk = documents[doc_id].chunks[chunk_id]
    
    # Extract key phrases from answer
    answer_phrases = extract_key_phrases(answer)
    
    # Check if phrases appear in cited chunk
    matches = sum(1 for phrase in answer_phrases if phrase in chunk.text)
    
    accuracy = matches / len(answer_phrases) if answer_phrases else 0
    return accuracy
```

#### Method C: Position Accuracy Test
```python
def test_start_index_accuracy(document: str, chunks: List[dict]):
    """
    Verify that start_index metadata is accurate.
    """
    errors = []
    
    for chunk in chunks:
        start_idx = chunk.metadata.get("start_index", 0)
        chunk_text = chunk.page_content
        
        # Check if chunk text matches document at start_idx
        doc_slice = document[start_idx:start_idx + len(chunk_text)]
        
        if doc_slice != chunk_text[:len(doc_slice)]:
            errors.append({
                "chunk_id": chunk.metadata.get("chunk_id"),
                "expected_start": start_idx,
                "actual_match": False
            })
    
    accuracy = 1 - (len(errors) / len(chunks))
    return accuracy, errors
```

### Target Metrics
- **Good:** Citation accuracy > 0.90 (90% of citations are correct)
- **Excellent:** Citation accuracy > 0.95 (95% of citations are correct)

---

## Comprehensive Evaluation Script

See `scripts/evaluate_chunking.py` for a complete evaluation tool.

### Usage:
```bash
python scripts/evaluate_chunking.py \
    --test-queries queries.json \
    --output results.json \
    --metrics all
```

---

## Evaluation Checklist

### Before Evaluation
- [ ] Prepare test dataset (10-20 diverse queries)
- [ ] Have ground truth answers ready
- [ ] Set up evaluation environment
- [ ] Prepare sample documents for boundary analysis

### During Evaluation
- [ ] Run retrieval precision tests
- [ ] Check context completeness for each query
- [ ] Review chunk boundaries in sample docs
- [ ] Verify citation accuracy

### After Evaluation
- [ ] Calculate aggregate metrics
- [ ] Identify common issues
- [ ] Document findings
- [ ] Propose improvements

---

## Interpreting Results

### If Retrieval Precision is Low (< 0.70)
- **Possible causes:** Chunks too large, poor embeddings, wrong k value
- **Solutions:** Reduce chunk size, improve embeddings, adjust retrieval k

### If Context Completeness is Low (< 0.75)
- **Possible causes:** Chunks too small, missing overlap, wrong retrieval
- **Solutions:** Increase chunk size, increase overlap, retrieve more chunks

### If Boundary Issues are High (> 10%)
- **Possible causes:** Poor separator priority, wrong chunk size
- **Solutions:** Adjust separators, use semantic chunking, increase overlap

### If Citation Accuracy is Low (< 0.90)
- **Possible causes:** Incorrect start_index, wrong chunk metadata
- **Solutions:** Fix chunking metadata, verify start_index calculation

---

## Continuous Monitoring

Set up automated evaluation:
- Run evaluation weekly/monthly
- Track metrics over time
- Alert on degradation
- A/B test chunking strategies

---

## References

- [LangChain Evaluation Guide](https://python.langchain.com/docs/guides/evaluation/)
- [RAG Evaluation Best Practices](https://www.pinecone.io/learn/rag-evaluation/)

