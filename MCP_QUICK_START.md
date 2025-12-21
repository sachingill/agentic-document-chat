# MCP Quick Start (Option A: proxy to FastAPI)

This project includes an **MCP (Model Context Protocol) server** that exposes your existing FastAPI backend as tools.

## Prereqs

- Backend API running locally (default): `http://127.0.0.1:8000`
- Python deps installed:

```bash
cd /Users/sachin/nltk_data/api
pip install -r requirements.txt
```

## Run the MCP server (stdio)

In a new terminal:

```bash
cd /Users/sachin/nltk_data/api
python scripts/mcp_server.py
```

By default it forwards tool calls to:
- `MCP_API_BASE_URL=http://127.0.0.1:8000`

Override if needed:

```bash
export MCP_API_BASE_URL="http://127.0.0.1:8000"
python scripts/mcp_server.py
```

## Exposed tools

- **`chat`**: routes to one of:
  - Structured: `POST /agent/chat`
  - Agentic: `POST /agentic/chat`
  - Multiagent: `POST /multiagent/chat`
- **`ingest_texts`**: `POST /agent/ingest/json`
- **`status`**: `GET /agent/debug/status`
- **`feedback`**: `POST /agent/feedback`

## Suggested client config (example)

Most MCP clients need:
- a **name**
- a **command** to launch the MCP server over stdio

Example command:

```bash
python /Users/sachin/nltk_data/api/scripts/mcp_server.py
```


