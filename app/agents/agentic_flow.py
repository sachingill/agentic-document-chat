from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.agents import tools as rag_tools
from app.agents.inference_modes import InferenceMode, INFERENCE_CONFIGS
from app.agents.inference_utils import expand_queries, verify_supported, IDK_SENTINEL, normalize_mixed_idk
from app.models import llm_factory


@dataclass
class AgenticResult:
    answer: str
    tools_used: List[str]
    retrieved_docs_count: int
    citations: List[Dict[str, Any]]


_TOOL_NAMES = [
    "retrieve",
    "keyword_search",
    "metadata_search",
    "summarize",
]


def _safe_json_loads(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except Exception:
        return {}


def _select_tool(question: str, iteration: int, context_hint: str) -> str:
    # Heuristic guardrail: always do semantic retrieval first to avoid empty-context cascades,
    # especially when using smaller/local models.
    if iteration == 1:
        return "retrieve"

    llm = llm_factory.fast_llm()
    prompt = f"""You are selecting the next tool for a RAG assistant.

Question: {question}
Iteration: {iteration}
Context hint (may be empty): {context_hint}

Choose exactly one tool from: {", ".join(_TOOL_NAMES)}

Rules:
- If you have little/no context, prefer "retrieve".
- If the question mentions exact terms/acronyms, consider "keyword_search".
- If the question asks for a specific attribute (date, owner, id), consider "metadata_search".
- If you already have enough context and need to condense it, use "summarize".

Return JSON ONLY:
{{"tool":"<one_of_tools>","reason":"<short>"}}
"""
    raw = llm.invoke(prompt).content
    data = _safe_json_loads(raw)
    tool = (data.get("tool") or "").strip()
    if tool in _TOOL_NAMES:
        return tool
    return "retrieve"


def _tool_call(tool: str, question: str) -> Dict[str, Any]:
    if tool == "retrieve":
        return rag_tools.retrieve_tool(question)
    if tool == "keyword_search":
        return rag_tools.keyword_search_tool(question)
    if tool == "metadata_search":
        # Best-effort: try to treat the whole question as a metadata search hint is too risky here,
        # so do a safe no-op unless caller provides explicit key/value (not supported in this lite flow).
        return {"key": None, "value": None, "results": [], "count": 0}
    if tool == "summarize":
        return rag_tools.summarize_tool(question)
    return {}


def run_agentic(question: str, *, max_iters: int = 3, inference_mode: InferenceMode = "balanced") -> AgenticResult:
    tools_used: List[str] = []
    documents: List[Dict[str, Any]] = []
    citations: List[Dict[str, Any]] = []
    context_hint = ""
    cfg = INFERENCE_CONFIGS.get(inference_mode, INFERENCE_CONFIGS["balanced"])

    for i in range(max_iters):
        tool = _select_tool(question=question, iteration=i + 1, context_hint=context_hint)
        tools_used.append(tool)
        out = _tool_call(tool, question)

        # Normalize tool outputs into `documents: [{text, ...}]`
        new_texts: List[str] = []
        if tool == "retrieve":
            # Prefer metadata-rich docs for citations
            docs = out.get("documents") or []
            if isinstance(docs, list) and docs:
                for d in docs:
                    if isinstance(d, dict) and isinstance(d.get("text"), str):
                        citations.append({"text": d.get("text", ""), "metadata": d.get("metadata") or {}})
                new_texts = [d.get("text", "") for d in docs if isinstance(d, dict)]
            else:
                new_texts = list(out.get("results") or [])
        elif tool == "keyword_search":
            new_texts = list(out.get("matches") or [])
        elif tool == "metadata_search":
            new_texts = list(out.get("results") or [])
        elif tool == "summarize":
            summary = (out.get("summary") or "").strip()
            if summary:
                new_texts = [summary]

        for t in new_texts:
            if isinstance(t, str) and t.strip():
                documents.append({"text": t})

        # keep a small evolving hint for tool selection
        if new_texts:
            snippet = []
            for t in new_texts[:3]:
                if isinstance(t, str) and t.strip():
                    snippet.append(t[:200])
            context_hint = "\n---\n".join(snippet)

        # stop early if we have some context and already summarized
        if tool == "summarize" and documents:
            break

    # Second-pass retrieval if we still have thin evidence
    if len(documents) < cfg.min_chunks:
        tools_used.append("retrieve(second_pass)")
        for q in expand_queries(question, mode=inference_mode)[1:]:
            res = rag_tools.retrieve_tool(q, k=cfg.second_pass_k)
            docs2 = res.get("documents") or []
            if isinstance(docs2, list) and docs2:
                for d in docs2:
                    if isinstance(d, dict) and isinstance(d.get("text"), str) and d.get("text", "").strip():
                        documents.append({"text": d.get("text", "")})
                        citations.append({"text": d.get("text", ""), "metadata": d.get("metadata") or {}})
            else:
                for t in (res.get("results") or []):
                    if isinstance(t, str) and t.strip():
                        documents.append({"text": t})

    # build final context
    ctx_parts: List[str] = []
    for d in documents[:12]:
        txt = (d.get("text") or "").strip()
        if txt:
            ctx_parts.append(txt)
    context = "\n\n---\n\n".join(ctx_parts)

    # Evidence gate (high): require minimum context before answering
    if inference_mode == "high" and len(ctx_parts) < cfg.min_chunks:
        return AgenticResult(answer=IDK_SENTINEL, tools_used=tools_used, retrieved_docs_count=len(documents))

    llm = llm_factory.main_llm()
    final_prompt = f"""Answer the question using ONLY the Context.
If the Context is insufficient, say: "I don't know based on the documents."

Question:
{question}

Context:
{context}
"""
    answer = llm.invoke(final_prompt).content.strip()
    answer = normalize_mixed_idk(answer)

    # Optional verifier (balanced/high)
    if cfg.verify_answer and answer != IDK_SENTINEL and context.strip():
        verdict = verify_supported(question=question, context=context[:8000], answer=answer)
        if verdict.get("supported") is False:
            answer = IDK_SENTINEL

    # Deduplicate citations by chunk_id (if present) or by text prefix
    seen: set[str] = set()
    deduped: list[Dict[str, Any]] = []
    for c in citations:
        meta = c.get("metadata") or {}
        key = meta.get("chunk_id") or (c.get("text", "")[:120])
        if key and key not in seen:
            seen.add(key)
            deduped.append({"text": c.get("text", "")[:500], "metadata": meta})

    return AgenticResult(
        answer=answer,
        tools_used=tools_used,
        retrieved_docs_count=len(documents),
        citations=deduped[:5],
    )


