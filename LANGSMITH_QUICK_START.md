# LangSmith Quick Start

## 🚀 Quick Setup (3 Steps)

### 1. Install Package
```bash
pip install langsmith
```

### 2. Get API Key
1. Go to https://smith.langchain.com
2. Sign up / Log in
3. Settings → API Keys → Create New Key
4. Copy the key

### 3. Add to `.env` File
```bash
LANGSMITH_API_KEY=your-api-key-here
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=rag-api
```

## ✅ That's It!

All LangChain/LangGraph components will automatically send traces to LangSmith.

## 📊 View Your Traces

1. Go to https://smith.langchain.com
2. Click "Traces" in the sidebar
3. See all your API requests in real-time!

## 🔍 What Gets Traced Automatically

- ✅ All `ChatOpenAI` calls (LLM invocations)
- ✅ LangGraph agent executions
- ✅ Vector database retrievals
- ✅ Functions with `@traceable` decorator

## 📝 Functions with Explicit Tracing

- `run_document_agent()` - Full RAG pipeline
- `retrieve_node()` - Document retrieval
- `generate_node()` - Answer generation
- `rerank()` - Document reranking
- `retrieve_tool()` - Vector search
- `check_input_safety()` - Input guardrails
- `check_output_safety()` - Output guardrails

## 🎯 Next Steps

- Read `LANGSMITH_SETUP.md` for detailed explanation
- Check LangSmith dashboard for metrics
- Set up alerts for errors/high latency
- Review traces to optimize prompts

