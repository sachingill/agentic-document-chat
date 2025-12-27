# Quick Start: Evaluating Chunking Strategy

## 1. Manual Evaluation (No Code Required)

### Retrieval Precision
1. Run 10-20 queries through your RAG system
2. For each query, review the top 3-5 retrieved chunks
3. Mark each chunk as "Relevant" or "Not Relevant"
4. Calculate: `Precision = Relevant Chunks / Total Chunks`

**Example:**
- Query: "What is authentication?"
- Retrieved: 5 chunks
- Relevant: 4 chunks
- **Precision = 4/5 = 80%** ✅

### Context Completeness
1. Create questions with known answers
2. Generate answers using RAG
3. Check if answer contains all required information
4. Calculate: `Completeness = Found Entities / Expected Entities`

**Example:**
- Question: "What are the three authentication methods?"
- Expected: ["OAuth2", "JWT", "API Key"]
- Answer contains: ["OAuth2", "JWT"]
- **Completeness = 2/3 = 67%** ⚠️

### Boundary Issues
1. Review sample documents after chunking
2. Look for:
   - Sentences split mid-way
   - Lists/enumerations broken
   - Code blocks split
3. Count issues per 100 chunks

**Example:**
- Document has 50 chunks
- Found 3 boundary issues
- **Issue Rate = 3/50 = 6%** ✅

### Citation Accuracy
1. Generate answers with citations
2. Verify each citation:
   - Does the chunk contain the information?
   - Is the document name correct?
   - Is the position accurate?
3. Calculate: `Accuracy = Correct Citations / Total Citations`

**Example:**
- 10 citations checked
- 9 are accurate
- **Accuracy = 9/10 = 90%** ✅

## 2. Automated Evaluation (Using Script)

### Setup
```bash
# Install dependencies (if needed)
pip install sentence-transformers scikit-learn

# Run evaluation
python scripts/evaluate_chunking.py \
    --test-queries samples/chunking_test_queries.json \
    --output evaluation_results.json
```

### Expected Output
```
============================================================
CHUNKING EVALUATION RESULTS
============================================================

📊 Retrieval Precision: 85.00% (n=10)
📋 Completeness: 78.00% (n=10)
🔗 Boundary Issues: 5.00% (3/60 chunks)
📍 Citation Accuracy: 92.00% (n=10)
🔗 Semantic Coherence: 88.00% (n=10)

✅ Results saved to evaluation_results.json
```

## 3. Target Metrics

| Metric | Good | Excellent |
|--------|------|-----------|
| Retrieval Precision | > 70% | > 85% |
| Completeness | > 75% | > 90% |
| Boundary Issues | < 10% | < 5% |
| Citation Accuracy | > 90% | > 95% |

## 4. What to Do If Metrics Are Low

### Low Retrieval Precision (< 70%)
- **Try:** Reduce chunk size (e.g., 600 chars)
- **Try:** Increase overlap (e.g., 240 chars)
- **Try:** Adjust retrieval k value

### Low Completeness (< 75%)
- **Try:** Increase chunk size (e.g., 1200 chars)
- **Try:** Retrieve more chunks (k=5-10)
- **Try:** Increase overlap

### High Boundary Issues (> 10%)
- **Try:** Adjust separator priority
- **Try:** Increase overlap
- **Try:** Use semantic chunking

### Low Citation Accuracy (< 90%)
- **Check:** Verify start_index calculation
- **Check:** Ensure chunk metadata is correct
- **Fix:** Update chunking code if needed

## 5. Continuous Monitoring

Run evaluation monthly:
```bash
# Save results with timestamp
python scripts/evaluate_chunking.py \
    --test-queries queries.json \
    --output results/$(date +%Y%m%d)_evaluation.json
```

Track trends over time to detect degradation.

## Next Steps

- Read **[CHUNKING_EVALUATION.md](./CHUNKING_EVALUATION.md)** for detailed methods
- Customize test queries for your domain
- Set up automated evaluation pipeline
