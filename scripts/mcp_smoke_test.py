"""
Smoke test for the MCP stdio server.

This spawns the MCP server as a subprocess (stdio transport), initializes the MCP session,
lists tools, and calls the `chat` tool (help query) which should be served by the backend.

Prereqs:
- Backend running at MCP_API_BASE_URL (default http://127.0.0.1:8000)
"""

from __future__ import annotations

import os
import sys

import anyio

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


async def main() -> None:
    base_url = os.getenv("MCP_API_BASE_URL", "http://127.0.0.1:8000")

    params = StdioServerParameters(
        command=sys.executable,
        args=["scripts/mcp_server.py"],
        env={**os.environ, "MCP_API_BASE_URL": base_url},
    )

    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            init = await session.initialize()
            tools = await session.list_tools()

            print("initialized:", init.serverInfo.name, init.serverInfo.version)
            print("tools:", [t.name for t in tools.tools])

            res = await session.call_tool(
                "chat",
                {
                    "question": "what can you do?",
                    "workflow": "structured",
                    "session_id": "mcp-smoke",
                    "inference_mode": "balanced",
                },
            )
            # Return is MCP content parts; our server returns JSON in a single text part.
            print("chat isError:", res.isError)
            print("chat content[0]:", res.content[0].text if res.content else None)


if __name__ == "__main__":
    anyio.run(main)


