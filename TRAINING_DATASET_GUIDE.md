# Training Dataset Guide

## Overview

This guide explains the high-quality training dataset created for testing RAG accuracy and how to use it.

---

## Dataset Components

### 1. Training Documents (`samples/training_documents.json`)

**Purpose:** High-quality documents covering diverse topics for ingestion into vector DB.

**Characteristics:**
- ✅ **20 documents** covering 10+ categories
- ✅ **Structured content** with clear information
- ✅ **Rich metadata** (doc_id, title, category, tags)
- ✅ **Diverse topics**: Authentication, Errors, Database, API, Security, Performance, RCA, etc.
- ✅ **Real-world scenarios**: Based on actual system documentation patterns

**Document Structure:**
```json
{
  "doc_id": "doc_auth_001",
  "title": "Authentication System Overview",
  "content": "Detailed content here...",
  "category": "authentication",
  "tags": ["auth", "security", "oauth2"]
}
```

**Categories Covered:**
1. **Authentication** (3 docs): OAuth2, JWT, API keys, OTP
2. **Error Handling** (2 docs): Error levels, database timeouts
3. **Database** (1 doc): Connection management
4. **API** (2 docs): Rate limiting, endpoints
5. **Security** (1 doc): Best practices
6. **Performance** (2 docs): Optimization, caching
7. **RCA** (2 docs): Process, error patterns
8. **Monitoring** (1 doc): Metrics and observability
9. **Deployment** (1 doc): CI/CD process
10. **Logging** (1 doc): Logging standards
11. **Testing** (1 doc): Testing strategy
12. **Download** (1 doc): File download system

### 2. Test Queries (`samples/training_queries_with_answers.json`)

**Purpose:** Test queries with ground truth answers for evaluation.

**Characteristics:**
- ✅ **20 test queries** with expected answers
- ✅ **Ground truth data**: Expected answers, entities, doc IDs
- ✅ **Difficulty levels**: Easy, Medium, Hard
- ✅ **Answer types**: List, Process, Configuration, Troubleshooting, etc.
- ✅ **Category coverage**: Matches document categories

**Query Structure:**
```json
{
  "query": "What are the three main authentication methods?",
  "expected_answer": "The three main authentication methods are OAuth2, JWT tokens, and API keys.",
  "expected_entities": ["OAuth2", "JWT", "API keys"],
  "expected_doc_ids": ["doc_auth_001"],
  "difficulty": "easy",
  "category": "authentication",
  "answer_type": "list"
}
```

**Query Distribution:**
- **Easy**: 10 queries (factual, simple)
- **Medium**: 8 queries (process, configuration)
- **Hard**: 2 queries (complex analysis)

---

## Quality Principles Applied

### 1. **Diversity**
- ✅ Multiple categories (10+ topics)
- ✅ Different question types (what, how, why)
- ✅ Various answer formats (lists, processes, facts)
- ✅ Different difficulty levels

### 2. **Realism**
- ✅ Based on real system documentation patterns
- ✅ Covers actual use cases (RCA, authentication, errors)
- ✅ Includes technical terminology
- ✅ Matches production scenarios

### 3. **Completeness**
- ✅ Each query has expected answer
- ✅ Expected entities for completeness checking
- ✅ Expected doc IDs for citation verification
- ✅ Difficulty and category tags

### 4. **Coverage**
- ✅ Covers all major system components
- ✅ Includes edge cases (error handling, troubleshooting)
- ✅ Mix of simple and complex queries
- ✅ Different answer types

---

## How to Use

### Step 1: Ingest Training Documents

```bash
# Ingest training documents into vector DB
python scripts/ingest_training_dataset.py \
    --documents samples/training_documents.json
```

**What it does:**
1. ✅ Loads 20 training documents
2. ✅ Extracts content and metadata
3. ✅ Ingests into vector DB with rich metadata
4. ✅ Shows summary by category

**Expected Output:**
```
📄 Loading training documents...
✅ Loaded 20 training documents

📊 Dataset Summary:
  • api: 2 documents
  • authentication: 3 documents
  • database: 1 document
  • deployment: 1 document
  • download: 1 document
  • error-handling: 2 documents
  • logging: 1 document
  • monitoring: 1 document
  • performance: 2 documents
  • rca: 2 documents
  • security: 1 document
  • testing: 1 document

🔄 Ingesting 20 documents into vector DB...
✅ Successfully ingested 20 training documents
```

### Step 2: Run Evaluation

```bash
# Evaluate using test queries
python scripts/evaluate_chunking_real.py \
    --test-queries samples/training_queries_with_answers.json \
    --output evaluation_results.json
```

**What it does:**
1. ✅ Queries actual RAG system with test queries
2. ✅ Retrieves real chunks from vector DB
3. ✅ Evaluates retrieval precision
4. ✅ Checks completeness (if expected entities provided)
5. ✅ Detects boundary issues
6. ✅ Generates evaluation report

### Step 3: Manual Testing

**Via UI:**
1. Go to Streamlit UI → Knowledge Base
2. Try queries from `training_queries_with_answers.json`
3. Compare answers with expected answers
4. Verify citations point to correct documents

**Via API:**
```bash
# Test a query
curl -X POST http://localhost:8000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the three main authentication methods?",
    "session_id": "test"
  }'
```

---

## Evaluation Metrics

### 1. Retrieval Precision
- **Target**: > 80% (8 out of 10 retrieved chunks are relevant)
- **How to measure**: Check if retrieved chunks contain expected entities

### 2. Answer Completeness
- **Target**: > 85% (answer contains most expected entities)
- **How to measure**: Compare answer with expected entities list

### 3. Citation Accuracy
- **Target**: > 90% (citations point to correct documents)
- **How to measure**: Verify citations match expected_doc_ids

### 4. Answer Quality
- **Target**: Answers match expected answers semantically
- **How to measure**: Manual review or LLM-based comparison

---

## Dataset Statistics

### Documents
- **Total**: 20 documents
- **Categories**: 12 categories
- **Average length**: ~200 words per document
- **Total words**: ~4,000 words

### Test Queries
- **Total**: 20 queries
- **Easy**: 10 queries (50%)
- **Medium**: 8 queries (40%)
- **Hard**: 2 queries (10%)
- **Categories**: 10 categories covered

### Coverage
- ✅ Authentication: 4 queries
- ✅ Error Handling: 2 queries
- ✅ Database: 1 query
- ✅ API: 2 queries
- ✅ Security: 2 queries
- ✅ Performance: 2 queries
- ✅ RCA: 2 queries
- ✅ Monitoring: 1 query
- ✅ Deployment: 1 query
- ✅ Logging: 1 query
- ✅ Testing: 1 query

---

## Adding More Documents

### Guidelines

1. **Content Quality**
   - Clear, structured information
   - Complete sentences
   - Technical accuracy
   - Real-world relevance

2. **Metadata**
   - Unique doc_id
   - Descriptive title
   - Relevant category
   - Useful tags

3. **Length**
   - 100-300 words per document
   - Enough context for retrieval
   - Not too long (chunking will split)

4. **Diversity**
   - Cover different topics
   - Mix of technical and conceptual
   - Various difficulty levels

### Example Template

```json
{
  "doc_id": "doc_category_XXX",
  "title": "Descriptive Title",
  "content": "Clear, structured content with key information. Include specific details, numbers, and examples. Make it realistic and useful.",
  "category": "category-name",
  "tags": ["tag1", "tag2", "tag3"]
}
```

---

## Adding More Test Queries

### Guidelines

1. **Query Quality**
   - Natural language questions
   - Clear intent
   - Answerable from documents
   - Varied question types

2. **Expected Answer**
   - Accurate and complete
   - Based on document content
   - Concise but informative

3. **Expected Entities**
   - Key terms/concepts from answer
   - Specific numbers/dates
   - Important names/identifiers

4. **Expected Doc IDs**
   - Documents that should be retrieved
   - Primary source document
   - May include multiple docs

### Example Template

```json
{
  "query": "Natural language question?",
  "expected_answer": "Complete answer based on documents.",
  "expected_entities": ["entity1", "entity2", "number"],
  "expected_doc_ids": ["doc_id_001"],
  "difficulty": "easy|medium|hard",
  "category": "category-name",
  "answer_type": "list|process|fact|configuration|troubleshooting"
}
```

---

## Best Practices

### For Document Creation

1. ✅ **Be Specific**: Include numbers, names, specific details
2. ✅ **Be Complete**: Cover the topic fully
3. ✅ **Be Realistic**: Use real-world scenarios
4. ✅ **Be Structured**: Clear organization, headings implied
5. ✅ **Be Diverse**: Cover different aspects

### For Query Creation

1. ✅ **Be Natural**: Use conversational language
2. ✅ **Be Specific**: Ask for concrete information
3. ✅ **Be Varied**: Different question types (what, how, why)
4. ✅ **Be Testable**: Answer should be verifiable
5. ✅ **Be Realistic**: Questions users would actually ask

---

## Troubleshooting

### Documents Not Retrieved

**Possible causes:**
- Query doesn't match document content semantically
- Chunking split important information
- Embedding model limitations

**Solutions:**
- Try rephrasing query
- Check if document was actually ingested
- Verify document content matches query intent

### Low Precision Scores

**Possible causes:**
- Generic embeddings not optimal
- Chunking strategy issues
- Query-document mismatch

**Solutions:**
- Consider DPR for better retrieval
- Adjust chunking parameters
- Improve query formulation

### Low Completeness Scores

**Possible causes:**
- Answer missing key information
- Chunks too small
- Not enough chunks retrieved

**Solutions:**
- Increase retrieval k value
- Adjust chunk size
- Improve document coverage

---

## Next Steps

1. ✅ **Ingest dataset**: Run ingestion script
2. ✅ **Run evaluation**: Test with evaluation script
3. ✅ **Analyze results**: Review precision, completeness, citations
4. ✅ **Iterate**: Add more documents/queries based on gaps
5. ✅ **Fine-tune**: Adjust chunking/retrieval based on results

---

## Files Created

- ✅ `samples/training_documents.json` - 20 high-quality documents
- ✅ `samples/training_queries_with_answers.json` - 20 test queries with ground truth
- ✅ `scripts/ingest_training_dataset.py` - Ingestion script
- ✅ `TRAINING_DATASET_GUIDE.md` - This guide

---

## Summary

**Training Dataset:**
- 📄 **20 documents** across 12 categories
- 📋 **20 test queries** with ground truth answers
- ✅ **High quality**: Realistic, diverse, complete
- ✅ **Well-structured**: Rich metadata, clear organization
- ✅ **Evaluation-ready**: Includes expected answers and entities

**Usage:**
```bash
# 1. Ingest documents
python scripts/ingest_training_dataset.py

# 2. Evaluate
python scripts/evaluate_chunking_real.py --test-queries samples/training_queries_with_answers.json
```

This dataset provides a solid foundation for testing and improving your RAG system accuracy!

