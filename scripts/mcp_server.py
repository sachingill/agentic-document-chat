"""
MCP (Model Context Protocol) server for this project (Option A).

This is a thin MCP wrapper that exposes your existing FastAPI backend as tools.
It speaks MCP over stdio and forwards tool calls to the running backend API.

Prereqs:
- Backend running: http://127.0.0.1:8000 (default)
- Install deps: pip install -r requirements.txt

Env:
- MCP_API_BASE_URL: base URL for the backend (default: http://127.0.0.1:8000)
"""

from __future__ import annotations

import json
import os
from typing import Any, Literal, Optional, Sequence

import anyio
import httpx

import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

Workflow = Literal["structured", "agentic", "multiagent"]
MultiAgentPattern = Literal["auto", "sequential", "parallel", "supervisor"]


API_BASE_URL = os.getenv("MCP_API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")

server = Server("agentic-document-chat")


async def _post(path: str, payload: dict[str, Any], *, timeout_s: float = 60) -> dict[str, Any]:
    url = f"{API_BASE_URL}{path}"
    async with httpx.AsyncClient(timeout=timeout_s) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data if isinstance(data, dict) else {"data": data}


async def _get(path: str, *, timeout_s: float = 30) -> dict[str, Any]:
    url = f"{API_BASE_URL}{path}"
    async with httpx.AsyncClient(timeout=timeout_s) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()
        return data if isinstance(data, dict) else {"data": data}


_TOOLS: list[types.Tool] = [
    types.Tool(
        name="chat",
        description=(
            "Ask a question to the backend chat system. "
            "Use workflow='structured' for strict doc-grounded RAG, "
            "'agentic' for tool-using agentic mode, and 'multiagent' for multi-agent orchestration."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "question": {"type": "string"},
                "session_id": {"type": "string", "default": "default"},
                "workflow": {
                    "type": "string",
                    "enum": ["structured", "agentic", "multiagent"],
                    "default": "structured",
                },
                "inference_mode": {"type": "string", "enum": ["low", "balanced", "high"], "default": "balanced"},
                "reset_session": {"type": "boolean", "default": False},
                # Agentic-only
                "max_iters": {"type": "integer", "default": 3, "minimum": 1, "maximum": 6},
                # Multiagent-only
                "auto_select_pattern": {"type": "boolean", "default": True},
                "pattern": {"type": "string", "enum": ["auto", "sequential", "parallel", "supervisor"], "default": "auto"},
                "max_relative_cost": {"type": ["number", "null"]},
                "max_relative_latency": {"type": ["number", "null"]},
            },
            "required": ["question"],
        },
    ),
    types.Tool(
        name="ingest_texts",
        description="Ingest raw texts into the vector DB for retrieval (Structured RAG ingestion).",
        inputSchema={
            "type": "object",
            "properties": {
                "texts": {"type": "array", "items": {"type": "string"}},
                "metadatas": {"type": ["array", "null"], "items": {"type": "object"}},
            },
            "required": ["texts"],
        },
    ),
    types.Tool(
        name="status",
        description="Check backend/vector DB status and a sample retrieval test.",
        inputSchema={"type": "object", "properties": {}},
    ),
    types.Tool(
        name="feedback",
        description="Send feedback (thumbs up/down + optional comment) for a question/answer pair.",
        inputSchema={
            "type": "object",
            "properties": {
                "session_id": {"type": "string"},
                "question": {"type": "string"},
                "answer": {"type": "string"},
                "thumbs_up": {"type": ["boolean", "null"]},
                "comment": {"type": ["string", "null"]},
                "expected_answer": {"type": ["string", "null"]},
            },
            "required": ["session_id", "question", "answer"],
        },
    ),
]


@server.list_tools()
async def _list_tools() -> list[types.Tool]:
    return _TOOLS


@server.call_tool()
async def _call_tool(name: str, arguments: dict[str, Any]) -> Sequence[types.TextContent]:
    def _as_text_content(obj: Any) -> Sequence[types.TextContent]:
        return [types.TextContent(type="text", text=json.dumps(obj, ensure_ascii=False))]

    async def _handle_chat(args: dict[str, Any]) -> dict[str, Any]:
        question = args.get("question")
        workflow: Workflow = args.get("workflow", "structured")
        session_id = args.get("session_id", "default")
        inference_mode = args.get("inference_mode", "balanced")

        if workflow == "agentic":
            return await _post(
                "/agentic/chat",
                {
                    "question": question,
                    "session_id": session_id,
                    "max_iters": int(args.get("max_iters", 3)),
                    "inference_mode": inference_mode,
                },
            )

        if workflow == "multiagent":
            payload: dict[str, Any] = {
                "question": question,
                "session_id": session_id,
                "auto_select_pattern": bool(args.get("auto_select_pattern", True)),
                "inference_mode": inference_mode,
            }
            if args.get("pattern") is not None:
                payload["pattern"] = args.get("pattern")
            if args.get("max_relative_cost") is not None:
                payload["max_relative_cost"] = args.get("max_relative_cost")
            if args.get("max_relative_latency") is not None:
                payload["max_relative_latency"] = args.get("max_relative_latency")
            return await _post("/multiagent/chat", payload)

        # structured
        return await _post(
            "/agent/chat",
            {
                "question": question,
                "session_id": session_id,
                "reset_session": bool(args.get("reset_session", False)),
                "inference_mode": inference_mode,
            },
        )

    async def _handle_status(_: dict[str, Any]) -> dict[str, Any]:
        return await _get("/agent/debug/status", timeout_s=30)

    async def _handle_ingest(args: dict[str, Any]) -> dict[str, Any]:
        return await _post(
            "/agent/ingest/json",
            {"texts": args.get("texts"), "metadatas": args.get("metadatas")},
            timeout_s=120,
        )

    async def _handle_feedback(args: dict[str, Any]) -> dict[str, Any]:
        return await _post(
            "/agent/feedback",
            {
                "session_id": args.get("session_id"),
                "question": args.get("question"),
                "answer": args.get("answer"),
                "thumbs_up": args.get("thumbs_up"),
                "comment": args.get("comment"),
                "expected_answer": args.get("expected_answer"),
            },
            timeout_s=30,
        )

    handlers: dict[str, Any] = {
        "status": _handle_status,
        "ingest_texts": _handle_ingest,
        "feedback": _handle_feedback,
        "chat": _handle_chat,
    }

    handler = handlers.get(name)
    if handler is None:
        raise ValueError(f"Unknown tool: {name}")

    result = await handler(arguments)
    return _as_text_content(result)


async def _main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    anyio.run(_main)


