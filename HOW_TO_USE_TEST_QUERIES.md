# How to Use Test Queries for Chunking Evaluation

## Overview

There are **two different evaluation approaches**, each with different test query formats:

1. **Mock Evaluation** (`evaluate_chunking.py`) - Uses pre-retrieved chunks (for testing the evaluation logic)
2. **Real Evaluation** (`evaluate_chunking_real.py`) - Actually queries your RAG system (for real evaluation)

---

## Approach 1: Real Evaluation (Recommended)

### What You Need

1. **Documents already ingested** in your vector database
2. **Simple test queries** (just questions, no pre-retrieved chunks)

### Step 1: Ingest Documents First

```bash
# Option A: Ingest sample error logs
python scripts/ingest_sample_logs.py

# Option B: Ingest via UI
# Go to Streamlit UI → Knowledge Base → Upload documents

# Option C: Ingest via API
curl -X POST http://localhost:8000/agent/ingest/json \
  -H "Content-Type: application/json" \
  -d '{"texts": ["Your document text here..."]}'
```

### Step 2: Create Simple Test Queries

Create a JSON file with just questions:

```json
[
  {
    "query": "What is authentication?",
    "expected_entities": ["authentication", "credentials"]
  },
  {
    "query": "How does error handling work?",
    "expected_entities": ["error", "exception"]
  }
]
```

**File:** `samples/test_queries_simple.json` (already created)

### Step 3: Run Real Evaluation

```bash
# Evaluate using actual RAG system
python scripts/evaluate_chunking_real.py \
    --test-queries samples/test_queries_simple.json \
    --output evaluation_results.json
```

**What it does:**
1. ✅ Queries your **actual vector database**
2. ✅ Retrieves **real chunks** from your ingested documents
3. ✅ Evaluates **actual retrieval precision**
4. ✅ Checks **real boundary issues** in your chunks
5. ✅ Verifies **completeness** if expected entities provided

### Example Output

```
📊 Vector DB contains 50 documents

[1/5] Evaluating: What is authentication?...
  ✅ Retrieved 5 chunks, Precision: 85.00%

[2/5] Evaluating: How does error handling work?...
  ✅ Retrieved 5 chunks, Precision: 80.00%

============================================================
CHUNKING EVALUATION RESULTS
============================================================

📊 Average Retrieval Precision: 82.50%
   (Based on 5 queries)

📋 Average Completeness: 75.00%
   (Based on 5 queries)

🔗 Boundary Issue Rate: 6.00%
   (3 issues in 50 chunks)

📚 Total Chunks Retrieved: 25

✅ Detailed results saved to evaluation_results.json
```

---

## Approach 2: Mock Evaluation (For Testing)

### What It's For

The `evaluate_chunking.py` script uses **mock data** - it doesn't query your actual system. It's useful for:
- Testing the evaluation logic
- Understanding how evaluation works
- Quick prototyping

### Test Query Format (Mock)

```json
[
  {
    "query": "What is authentication?",
    "retrieved_chunks": [
      "Authentication is the process...",
      "It involves checking credentials..."
    ],
    "answer": "Authentication verifies identity...",
    "expected_entities": ["authentication", "credentials"],
    "document_text": "Full document text...",
    "citations": [{"chunk_id": "doc_0::chunk_0", "start_index": 0}]
  }
]
```

**File:** `samples/chunking_test_queries.json` (example mock data)

### Run Mock Evaluation

```bash
python scripts/evaluate_chunking.py \
    --test-queries samples/chunking_test_queries.json \
    --output mock_results.json
```

**Note:** This doesn't query your actual system - it just evaluates the provided mock data.

---

## Comparison

| Feature | Real Evaluation | Mock Evaluation |
|---------|----------------|-----------------|
| **Queries actual DB** | ✅ Yes | ❌ No |
| **Uses real chunks** | ✅ Yes | ❌ No |
| **Test query format** | Simple (just questions) | Complex (pre-retrieved chunks) |
| **Use case** | Real evaluation | Testing evaluation logic |
| **Requires ingested docs** | ✅ Yes | ❌ No |

---

## Recommended Workflow

### For Real Evaluation:

1. **Ingest your documents** into the vector database
2. **Create simple test queries** (`test_queries_simple.json`)
3. **Run real evaluation:**
   ```bash
   python scripts/evaluate_chunking_real.py \
       --test-queries samples/test_queries_simple.json \
       --output results.json
   ```
4. **Review results** and adjust chunking strategy if needed

### For Testing Evaluation Logic:

1. **Use mock data** (`chunking_test_queries.json`)
2. **Run mock evaluation:**
   ```bash
   python scripts/evaluate_chunking.py \
       --test-queries samples/chunking_test_queries.json \
       --output mock_results.json
   ```

---

## Customizing Test Queries

### For Your Domain

Create test queries relevant to your documents:

```json
[
  {
    "query": "Your actual question here",
    "expected_entities": ["entity1", "entity2"]
  }
]
```

### Tips:

- **10-20 queries** is a good sample size
- **Mix simple and complex** questions
- **Cover different topics** from your documents
- **Include edge cases** (specific details, comparisons, etc.)

---

## Troubleshooting

### "No documents in vector DB"
```bash
# Ingest documents first
python scripts/ingest_sample_logs.py
# Or use UI/API to ingest your documents
```

### "No chunks retrieved"
- Check if your queries match document content
- Verify documents are actually ingested
- Try broader/more general queries

### "Low precision scores"
- Your chunking strategy may need adjustment
- Documents may not contain relevant information
- Try different query formulations

---

## Next Steps

1. ✅ Ingest your documents
2. ✅ Create test queries for your domain
3. ✅ Run real evaluation
4. ✅ Review results and adjust chunking if needed
5. ✅ Set up continuous monitoring

