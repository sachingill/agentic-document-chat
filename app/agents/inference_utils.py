from __future__ import annotations

import json
from typing import List, Dict, Any

from app.agents.inference_modes import InferenceMode, INFERENCE_CONFIGS
from app.models import llm_factory


IDK_SENTINEL = "I don't know based on the documents."

def normalize_mixed_idk(text: str) -> str:
    """
    Some models produce an answer and then append the IDK sentinel.
    If the sentinel appears, keep the content before it (if any); otherwise return sentinel.
    """
    if not text:
        return text
    if IDK_SENTINEL not in text:
        return text
    before = text.split(IDK_SENTINEL, 1)[0].strip()
    return before if before else IDK_SENTINEL


def _safe_json_list(text: str) -> List[str]:
    try:
        data = json.loads(text)
        if isinstance(data, list):
            out: List[str] = []
            for x in data:
                if isinstance(x, str) and x.strip():
                    out.append(x.strip())
            return out
    except Exception:
        return []
    return []


def expand_queries(question: str, *, mode: InferenceMode) -> List[str]:
    """
    Generate additional retrieval queries to improve recall.
    Output is intentionally short to avoid query drift.
    """
    cfg = INFERENCE_CONFIGS[mode]
    llm = llm_factory.fast_llm(temperature=0.0)
    prompt = f"""Generate {cfg.expansions} alternative search queries for semantic retrieval.

Original question:
{question}

Rules:
- Each query should be <= 12 words.
- Prefer acronyms expanded (if any).
- Prefer noun phrases and key constraints.
- Do NOT invent facts; keep meaning equivalent.

Return JSON list only.
"""
    raw = llm.invoke(prompt).content.strip()
    # remove code fences
    if "```" in raw:
        raw = raw.replace("```json", "").replace("```", "").strip()
    queries = _safe_json_list(raw)
    # Always include original question first
    dedup: List[str] = []
    seen = set()
    for q in [question] + queries:
        key = q.lower().strip()
        if key and key not in seen:
            seen.add(key)
            dedup.append(q.strip())
    return dedup[: 1 + cfg.expansions]


def verify_supported(*, question: str, context: str, answer: str) -> Dict[str, Any]:
    """
    Lightweight verifier: checks whether the answer is supported by provided context.
    Returns dict: {supported: bool, reason: str}
    """
    llm = llm_factory.fast_llm(temperature=0.0)
    prompt = f"""You are a strict verifier.

Question:
{question}

Context:
{context}

Answer:
{answer}

Decide if the Answer is fully supported by the Context.
If the answer includes claims not in the context, mark supported=false.

Return JSON only:
{{"supported": true|false, "reason": "<short>"}}
"""
    raw = llm.invoke(prompt).content.strip()
    if "```" in raw:
        raw = raw.replace("```json", "").replace("```", "").strip()
    try:
        data = json.loads(raw)
        supported = bool(data.get("supported"))
        reason = str(data.get("reason") or "").strip()
        return {"supported": supported, "reason": reason}
    except Exception:
        # Be conservative: if verifier fails, don't block in balanced/low.
        return {"supported": True, "reason": "verifier_parse_failed"}


