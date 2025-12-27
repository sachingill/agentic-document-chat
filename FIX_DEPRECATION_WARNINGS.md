# Fix Deprecation Warnings

## Issues Fixed

1. **LangChain Deprecation Warnings**
   - `HuggingFaceEmbeddings` deprecated → Use `langchain-huggingface`
   - `Chroma` deprecated → Use `langchain-chroma`

2. **LangSmith Warning**
   - `run_type="guardrail"` not recognized → Changed to `run_type="chain"`

3. **ChromaDB Error Handling**
   - Improved error detection for corruption
   - Better fallback handling

## Changes Made

### 1. Updated `app/models/embeddings.py`
- Added try/except to use new packages with fallback
- Improved ChromaDB corruption detection
- Changed error level from ERROR to WARNING for expected corruption

### 2. Updated `requirements.txt`
- Added `langchain-huggingface`
- Added `langchain-chroma`

### 3. Updated `app/agents/guardrails.py`
- Changed `run_type="guardrail"` → `run_type="chain"`

## Installation

Install the new packages:

```bash
pip install langchain-huggingface langchain-chroma
```

Or update all requirements:

```bash
pip install -r requirements.txt
```

## Notes

- The code will automatically fallback to deprecated packages if new ones aren't installed
- ChromaDB corruption errors are now handled gracefully with automatic fallback
- The system will create a fresh DB (`ragdb_fresh_<timestamp>`) when corruption is detected
