# Chunking Strategy for RAG and Agentic Systems

## Overview

Both **Structured RAG** and **Agentic RAG** systems use the **same chunking strategy** to ensure consistency across the knowledge base.

## Current Strategy

### Implementation

**Chunking Library:** `RecursiveCharacterTextSplitter` (LangChain)

**Configuration:**
```python
RecursiveCharacterTextSplitter(
    chunk_size=900,           # Maximum characters per chunk
    chunk_overlap=180,        # Overlap between chunks (20% of chunk_size)
    separators=["\n\n", "\n", ". ", " ", ""],  # Priority order for splitting
    add_start_index=True,     # Track character position in original document
)
```

### Parameters Explained

#### 1. **Chunk Size: 900 characters**
- **Rationale:** Balances context preservation with retrieval precision
- **Trade-off:** 
  - Too small (<500): Loses context, fragments meaning
  - Too large (>1500): Reduces retrieval precision, increases noise
- **900 chars** ≈ 150-200 words (good for most documents)

#### 2. **Chunk Overlap: 180 characters (20%)**
- **Purpose:** Prevents information loss at chunk boundaries
- **Benefit:** Ensures context continuity between chunks
- **Example:** If chunk ends mid-sentence, next chunk includes that sentence

#### 3. **Separator Priority**
The splitter tries separators in order until chunk size is met:

1. **`\n\n`** (Double newline) - Paragraph breaks
2. **`\n`** (Single newline) - Line breaks
3. **`. `** (Period + space) - Sentence boundaries
4. **` `** (Space) - Word boundaries
5. **`""`** (Empty) - Character-by-character (last resort)

**Why this order?**
- Preserves document structure (paragraphs → sentences → words)
- Maintains semantic coherence
- Avoids breaking mid-sentence when possible

#### 4. **Start Index Tracking**
- **`add_start_index=True`** adds metadata about character position
- **Use case:** Citations can reference exact document locations
- **Benefit:** Better traceability and debugging

## Where It's Used

### 1. Structured RAG (`app/models/embeddings.py`)
```python
def ingest_documents(texts: list[str], metadata=None):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=900,
        chunk_overlap=180,
        separators=["\n\n", "\n", ". ", " ", ""],
        add_start_index=True,
    )
    # ... chunking logic
```

### 2. Agentic RAG (`agentic/app/models/embeddings.py`)
```python
def ingest_documents(texts: list[str], metadata=None):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=900,
        chunk_overlap=180,
        separators=["\n\n", "\n", ". ", " ", ""],
        add_start_index=True,
    )
    # ... chunking logic
```

**Note:** Both systems share the same vector database (`ragdb`), so consistency is critical.

## Chunk Metadata

Each chunk includes:

```python
{
    "doc_id": "doc_0",                    # Original document ID
    "chunk_index": 0,                     # Position in document (0-indexed)
    "chunk_id": "doc_0::chunk_0",         # Unique chunk identifier
    "start_index": 0,                     # Character position in original doc
    # ... plus any custom metadata from ingestion
}
```

## Why This Strategy?

### ✅ Advantages

1. **Structure-Aware:** Preserves document hierarchy (paragraphs, sentences)
2. **Context Preservation:** Overlap prevents boundary information loss
3. **Consistent:** Same strategy across all systems
4. **Traceable:** Start index enables precise citations
5. **Balanced:** 900 chars is optimal for most use cases

### ⚠️ Limitations

1. **Fixed Size:** Doesn't adapt to document type (code vs. prose)
2. **No Semantic Boundaries:** May split related concepts
3. **Uniform:** Same strategy for all document types

## Alternative Strategies (Not Currently Used)

### 1. **Semantic Chunking**
- Uses embeddings to find semantic boundaries
- **Pros:** Better semantic coherence
- **Cons:** More complex, slower, requires additional model

### 2. **Token-Based Chunking**
- Uses token count instead of characters
- **Pros:** More accurate for LLM context windows
- **Cons:** Requires tokenizer, varies by model

### 3. **Document-Type Specific**
- Different strategies for PDFs, code, markdown, etc.
- **Pros:** Optimized per content type
- **Cons:** More complex, harder to maintain

### 4. **Sliding Window with Variable Overlap**
- Dynamic overlap based on content
- **Pros:** More adaptive
- **Cons:** Complex to implement

## Recommendations

### Current Strategy is Good For:
- ✅ General-purpose documents
- ✅ Mixed content types
- ✅ Consistent retrieval needs
- ✅ Simple maintenance

### Consider Alternatives If:
- 📊 You have specialized content (code, tables, structured data)
- 📊 You need semantic coherence (related concepts stay together)
- 📊 You're hitting retrieval quality issues
- 📊 You have very long documents (>10k chars)

## Tuning Parameters

If you need to adjust:

### For Longer Context Needs:
```python
chunk_size=1200,      # Increase size
chunk_overlap=240,    # Maintain 20% overlap
```

### For Better Precision:
```python
chunk_size=600,       # Smaller chunks
chunk_overlap=120,    # Maintain 20% overlap
```

### For Code/Structured Content:
```python
separators=["\n\n\n", "\n\n", "\n", " ", ""]  # Prioritize larger breaks
```

## Monitoring

Track these metrics to evaluate chunking effectiveness:

1. **Retrieval Precision:** Are retrieved chunks relevant?
2. **Context Completeness:** Do chunks contain full answers?
3. **Boundary Issues:** Are concepts split across chunks?
4. **Citation Accuracy:** Can citations point to exact locations?

### Evaluation Guide

See **[CHUNKING_EVALUATION.md](./CHUNKING_EVALUATION.md)** for detailed instructions on how to evaluate each metric, including:
- Step-by-step evaluation methods
- Automated evaluation scripts
- Target metrics and thresholds
- Interpretation guidelines

**Quick Start:**
```bash
python scripts/evaluate_chunking.py --test-queries queries.json --output results.json
```

## References

- **LangChain Docs:** [RecursiveCharacterTextSplitter](https://python.langchain.com/docs/modules/data_connection/document_transformers/recursive_text_splitter)
- **Chunking Best Practices:** [LangChain Chunking Guide](https://python.langchain.com/docs/modules/data_connection/document_transformers/)

