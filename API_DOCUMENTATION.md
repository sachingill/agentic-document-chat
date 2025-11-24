# API Documentation

This document provides comprehensive API documentation with sample curl commands for all endpoints.

**Base URL:** `http://localhost:8000` (default FastAPI port)

---

## Table of Contents

1. [Root Endpoint](#1-root-endpoint)
2. [User Endpoints](#2-user-endpoints)
3. [Prediction Endpoints](#3-prediction-endpoints)
4. [Agent Endpoints](#4-agent-endpoints)

---

## 1. Root Endpoint

### GET `/`

Check if the API is running.

**Request:**
```bash
curl -X GET "http://localhost:8000/" \
  -H "accept: application/json"
```

**Response:**
```json
{
  "message": "API is running"
}
```

---

## 2. User Endpoints

### GET `/users/{user_id}`

Get user information by ID.

**Request:**
```bash
curl -X GET "http://localhost:8000/users/123" \
  -H "accept: application/json"
```

**Response:**
```json
{
  "user_id": 123,
  "name": "Test User"
}
```

**Example with different ID:**
```bash
curl -X GET "http://localhost:8000/users/456"
```

---

## 3. Prediction Endpoints

### POST `/predict/`

Perform sentiment analysis on text. Returns positive/negative label with confidence score.

**Request:**
```bash
curl -X POST "http://localhost:8000/predict/" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "I love this product! It works perfectly."
  }'
```

**Response:**
```json
{
  "text": "I love this product! It works perfectly.",
  "label": "positive",
  "confidence": 0.9987
}
```

**Example with negative sentiment:**
```bash
curl -X POST "http://localhost:8000/predict/" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This is terrible and does not work at all."
  }'
```

**Response:**
```json
{
  "text": "This is terrible and does not work at all.",
  "label": "negative",
  "confidence": 0.9876
}
```

---

## 4. Agent Endpoints

### POST `/agent/ingest`

Upload and ingest documents into the vector database for RAG (Retrieval Augmented Generation).

**Request:**
```bash
curl -X POST "http://localhost:8000/agent/ingest" \
  -H "accept: application/json" \
  -F "files=@document1.txt" \
  -F "files=@document2.txt"
```

**Multiple files example:**
```bash
curl -X POST "http://localhost:8000/agent/ingest" \
  -F "files=@/path/to/document1.txt" \
  -F "files=@/path/to/document2.pdf" \
  -F "files=@/path/to/document3.md"
```

**Response:**
```json
{
  "status": "success",
  "files_ingested": 2
}
```

**Note:** 
- Supports multiple file uploads
- Files are processed and stored in the vector database
- Text files are automatically chunked and embedded

**Creating a test file for upload:**
```bash
# Create a test document
echo "This is a sample document about machine learning. Machine learning is a subset of artificial intelligence." > test_doc.txt

# Upload it
curl -X POST "http://localhost:8000/agent/ingest" \
  -F "files=@test_doc.txt"
```

**⚠️ zsh Terminal Users:**

If you're using zsh and encounter issues with the `@` symbol in file paths, try:

1. **Use single quotes:**
   ```bash
   curl -X POST "http://localhost:8000/agent/ingest" \
     -F 'files=@test_doc.txt'
   ```

2. **Use absolute path:**
   ```bash
   curl -X POST "http://localhost:8000/agent/ingest" \
     -F "files=@$(pwd)/test_doc.txt"
   ```

3. **For files with spaces, quote the path:**
   ```bash
   curl -X POST "http://localhost:8000/agent/ingest" \
     -F "files=@\"My Document.txt\""
   ```

See `CURL_EXAMPLES_ZSH.md` for detailed zsh-specific troubleshooting.

---

### POST `/agent/chat`

Chat with the RAG agent. Ask questions about the ingested documents. The agent maintains conversation history per session.

**Request Parameters:**
- `question` (required): The question to ask about the documents
- `session_id` (optional): Session identifier for maintaining conversation history. Defaults to "default" if not provided.

**Request (with default session):**
```bash
curl -X POST "http://localhost:8000/agent/chat" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is machine learning?"
  }'
```

**Request (with custom session):**
```bash
curl -X POST "http://localhost:8000/agent/chat" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "user-123",
    "question": "What is machine learning?"
  }'
```

**Response:**
```json
{
  "answer": "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed."
}
```

**More examples:**

```bash
# Ask a specific question with session
curl -X POST "http://localhost:8000/agent/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "conversation-1",
    "question": "Explain the main concepts discussed in the documents"
  }'
```

```bash
# Ask a follow-up question (same session maintains context)
curl -X POST "http://localhost:8000/agent/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "conversation-1",
    "question": "Can you provide more details about that?"
  }'
```

**Error Response (if question is missing):**
```json
{
  "error": "Missing 'question' field"
}
```

**Note:** 
- Each `session_id` maintains its own conversation history
- Use the same `session_id` for follow-up questions to maintain context
- Different `session_id` values create separate conversation threads

---

## Complete Workflow Example

Here's a complete workflow from document ingestion to querying:

```bash
# 1. Create sample documents
cat > doc1.txt << EOF
FastAPI is a modern web framework for building APIs with Python.
It is based on standard Python type hints and is very fast.
EOF

cat > doc2.txt << EOF
LangChain is a framework for developing applications powered by language models.
It provides tools for building RAG applications.
EOF

# 2. Ingest documents
curl -X POST "http://localhost:8000/agent/ingest" \
  -F "files=@doc1.txt" \
  -F "files=@doc2.txt"

# 3. Ask questions about the documents (using same session for context)
curl -X POST "http://localhost:8000/agent/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "my-session",
    "question": "What is FastAPI?"
  }'

curl -X POST "http://localhost:8000/agent/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "my-session",
    "question": "What is LangChain used for?"
  }'
```

---

## Running the Server

Before making API calls, start the FastAPI server:

```bash
# Activate virtual environment
source venv/bin/activate

# Run the server
uvicorn app.main:app --reload
```

The server will start at `http://localhost:8000`

**Alternative with custom port:**
```bash
uvicorn app.main:app --reload --port 8080
```

---

## Interactive API Documentation

FastAPI provides automatic interactive documentation:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

You can test all endpoints directly from the browser using these interfaces.

---

## Error Handling

### Common Error Responses

**400 Bad Request:**
```json
{
  "detail": "Invalid request format"
}
```

**422 Unprocessable Entity:**
```json
{
  "detail": [
    {
      "loc": ["body", "text"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Internal server error"
}
```

---

## Environment Setup

Make sure you have:

1. **`.env` file** with `OPENAI_API_KEY` set:
```bash
OPENAI_API_KEY=sk-your-actual-api-key-here
```

2. **All dependencies installed:**
```bash
pip install -r requirements.txt
```

3. **Vector database directory** (created automatically):
   - `./ragdb/` - ChromaDB persistence directory

---

## Notes

- The `/agent/chat` endpoint maintains conversation history per session
- Documents uploaded via `/agent/ingest` are stored persistently in the vector database
- The sentiment prediction model loads on first use (may take a few seconds)
- All endpoints return JSON responses
- File uploads support text files (.txt, .md, etc.)

---

## Troubleshooting

**Issue: API key not found**
- Ensure `.env` file exists with `OPENAI_API_KEY` set
- Restart the server after updating `.env`

**Issue: File upload fails**
- Ensure `python-multipart` is installed: `pip install python-multipart`
- Check file path and permissions

**Issue: Vector database errors**
- Ensure write permissions for `./ragdb/` directory
- Delete `./ragdb/` and restart if corrupted

**Issue: Model loading slow**
- First prediction may take time to load the model
- Subsequent requests will be faster

