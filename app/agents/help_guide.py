"""
Help / onboarding guide for the chat system.

This module MUST remain lightweight and must not import any LLM factories or vector DB code.
It is used to answer meta "what can you do / how do I use this?" queries even when retrieval is empty.
"""

from __future__ import annotations

import re
from typing import Literal


WorkflowName = Literal["structured", "agentic", "multiagent"]


_HELP_QUERY_PATTERNS: list[re.Pattern[str]] = [
    # Direct help intents
    re.compile(r"^\s*(help|/\?|\?)\s*$", re.IGNORECASE),
    re.compile(r"\b(what can you do|what do you do|your capabilities|capabilities)\b", re.IGNORECASE),
    re.compile(r"\b(how (can|do) (you|this) (help|work)|how to use|usage)\b", re.IGNORECASE),
    # "how to help ..." phrasing (common, but user is asking for usage/onboarding)
    re.compile(r"\bhow to\b.*\bhelp\b", re.IGNORECASE),
    # More flexible phrasing (e.g. "how this ... can help?")
    re.compile(r"\bhow\b.*\b(can|could)\b.*\bhelp\b", re.IGNORECASE),
    re.compile(r"\bhow\b.*\buse\b.*\b(this|it)\b", re.IGNORECASE),
    # "help guide/manual" phrasing
    re.compile(r"\b(help)\b.*\b(guide|manual|usage|use)\b", re.IGNORECASE),
    re.compile(r"\b(example prompts?|sample prompts?|give me examples?)\b", re.IGNORECASE),
    # Common onboarding questions
    re.compile(r"\b(what is this|what is this chat|what is this system)\b", re.IGNORECASE),
]


def is_help_query(text: str | None) -> bool:
    if not text:
        return False
    t = text.strip()
    if not t:
        return False
    return any(p.search(t) for p in _HELP_QUERY_PATTERNS)


def help_answer(*, workflow: WorkflowName = "structured") -> str:
    # Keep this fully static (not RAG-dependent) so it works even with an empty vector DB.
    workflow_line = {
        "structured": "You’re currently using **Structured RAG** (`POST /agent/chat`).",
        "agentic": "You’re currently using **Agentic RAG** (`POST /agentic/chat`).",
        "multiagent": "You’re currently using **Multi-agent RAG** (`POST /multiagent/chat`).",
    }[workflow]

    extra = ""
    if workflow == "agentic":
        extra = (
            "\n\n**Agentic tip**\n"
            "- This mode may run tools in steps (retrieve, refine, verify). If you want a quick answer, reduce `max_iters`."
        )
    elif workflow == "multiagent":
        extra = (
            "\n\n**Multi-agent tip**\n"
            "- You can let it auto-select a pattern, or force one: `sequential`, `parallel`, or `supervisor`."
        )

    return (
        "I’m a **document Q&A chat system (RAG)**. I help you upload/ingest documents, then answer questions "
        "grounded in those documents (and I’ll say when the docs don’t contain the answer).\n\n"
        f"{workflow_line}\n\n"
        "**What you can do**\n"
        "- Ingest content (text or files) so it becomes searchable\n"
        "- Ask questions and get answers based *only* on the ingested docs\n"
        "- Use `session_id` to keep conversation context; use `reset_session` to start fresh\n"
        "- Choose an `inference_mode`: `low` (faster), `balanced`, `high` (stricter; more likely to say “I don’t know”)\n\n"
        "**How to use it (typical flow)**\n"
        "1) Ingest docs → `POST /agent/ingest` (multipart) or `POST /agent/ingest/json`\n"
        "2) Chat/Q&A → call your chosen chat endpoint with `question` + optional `session_id`\n\n"
        "**Example questions you can ask after ingesting docs**\n"
        "- “Summarize the document in 5 bullets.”\n"
        "- “What are the key steps for <process>?”\n"
        "- “What does <term> mean in our docs? Quote the relevant section.”\n"
        "- “Compare X vs Y based on the docs.”\n"
        "- “List errors/edge cases mentioned and how to handle them.”\n"
        f"{extra}\n\n"
        "If you tell me what kind of docs you ingested (API docs, PDFs, tickets, runbooks, etc.), I can suggest "
        "the best prompts for your use-case."
    )


