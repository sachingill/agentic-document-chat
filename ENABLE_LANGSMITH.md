# Enable LangSmith Tracing

## Current Status
✅ API Key: **Set**  
❌ Tracing: **Disabled**

## Quick Fix

Add this line to your `.env` file:

```bash
LANGSMITH_TRACING=true
```

## Complete `.env` Configuration

Your `.env` file should have:

```bash
# OpenAI
OPENAI_API_KEY=your-openai-key

# LangSmith
LANGSMITH_API_KEY=your-langsmith-key
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=rag-api
LANGSMITH_TAGS=production,rag,api
```

## After Adding

1. **Restart your FastAPI server** (if running)
2. **Verify it's enabled**:
   ```bash
   python -c "from app.config import LangSmithConfig; print('Enabled:', LangSmithConfig.is_enabled())"
   ```
   Should print: `Enabled: True`

3. **Make a test request**:
   ```bash
   curl -X POST http://127.0.0.1:8000/agent/chat \
     -H "Content-Type: application/json" \
     -d '{"session_id": "test", "question": "Test", "reset_session": true}'
   ```

4. **Check LangSmith Dashboard**:
   - Go to https://smith.langchain.com
   - Click "Traces"
   - You should see your request appear!

## What Gets Traced

Once enabled, you'll see:
- ✅ All LLM calls (ChatOpenAI)
- ✅ Document retrieval
- ✅ Reranking operations
- ✅ Guardrail checks
- ✅ Full RAG pipeline execution
- ✅ Performance metrics
- ✅ Token usage and costs

