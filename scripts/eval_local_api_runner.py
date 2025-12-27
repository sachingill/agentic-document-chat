"""
Local API Evaluation Runner

Evaluates the running unified API (structured /agent, agentic /agentic, multiagent /multiagent)
on a JSONL eval set and computes:
- Answer quality (correctness, completeness)  [LLM-judge if expected_answer is present]
- Groundedness (supported by retrieved context) [LLM-judge via verifier]
- Retrieval quality (context relevance / sufficiency) [LLM-judge]
- Safety (guardrail signals + offline output guardrail)
- Latency (wall-clock)
- Cost (best-effort: relative estimates + fallback model mapping)

Optionally pushes runs + feedback into LangSmith if LANGSMITH_API_KEY is set.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple

import httpx

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

# Avoid HuggingFace tokenizer fork warnings in eval runs.
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

try:
    # Optional: only needed when EVAL_RUN_OFFLINE_GUARDRAILS=true.
    # Guardrails may require an LLM backend to be configured; keep eval runner usable even when not.
    from app.agents.guardrails import check_input_safety, check_output_safety  # type: ignore
except Exception:  # pragma: no cover
    def check_input_safety(_: str):  # type: ignore
        return None

    def check_output_safety(_: str):  # type: ignore
        return None
from app.agents.inference_modes import INFERENCE_CONFIGS, InferenceMode
from app.agents.inference_utils import verify_supported
from app.models.embeddings import get_retriever
from app.models import llm_factory


Workflow = Literal["structured", "agentic", "multiagent"]


@dataclass(frozen=True)
class EvalCase:
    id: str
    workflow: Workflow
    question: str
    inference_mode: InferenceMode = "balanced"
    expected_answer: Optional[str] = None
    # multiagent-only
    pattern: Optional[Literal["auto", "sequential", "parallel", "supervisor"]] = None


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def _load_cases(path: Path) -> List[EvalCase]:
    raw = _read_jsonl(path)
    cases: List[EvalCase] = []
    for i, r in enumerate(raw):
        cases.append(
            EvalCase(
                id=str(r.get("id") or f"case_{i}"),
                workflow=r["workflow"],
                question=r["question"],
                inference_mode=r.get("inference_mode", "balanced"),
                expected_answer=r.get("expected_answer"),
                pattern=r.get("pattern"),
            )
        )
    return cases


def _endpoint_for(case: EvalCase) -> Tuple[str, Dict[str, Any]]:
    if case.workflow == "structured":
        return "/agent/chat", {"question": case.question, "inference_mode": case.inference_mode}
    if case.workflow == "agentic":
        return "/agentic/chat", {
            "question": case.question,
            "max_iters": 3,
            "inference_mode": case.inference_mode,
        }
    # multiagent
    payload: Dict[str, Any] = {
        "question": case.question,
        "auto_select_pattern": True,
        "inference_mode": case.inference_mode,
    }
    if case.pattern and case.pattern != "auto":
        payload["auto_select_pattern"] = False
        payload["pattern"] = case.pattern
    return "/multiagent/chat", payload


def _retrieve_context(question: str, *, k: int) -> List[str]:
    retriever = get_retriever(k=k)
    if hasattr(retriever, "invoke"):
        docs = retriever.invoke(question)
    else:
        docs = retriever.get_relevant_documents(question)  # type: ignore[attr-defined]
    out: List[str] = []
    for d in docs:
        # doc is a langchain Document
        txt = getattr(d, "page_content", None)
        if isinstance(txt, str) and txt.strip():
            out.append(txt.strip())
    return out


def _llm_json(prompt: str) -> Dict[str, Any]:
    try:
        llm = llm_factory.fast_llm(temperature=0.0)
        raw = llm.invoke(prompt).content.strip()
        if "```" in raw:
            raw = raw.replace("```json", "").replace("```", "").strip()

        # Be resilient to models that wrap JSON with extra text.
        # Try to extract the first JSON object in the response.
        m = re.search(r"\{[\s\S]*\}", raw)
        if m:
            raw = m.group(0).strip()

        return json.loads(raw)
    except Exception:
        return {}


def score_answer_quality(*, question: str, answer: str, expected: Optional[str]) -> Dict[str, Any]:
    """
    Returns:
      {
        "correctness": float 0-1,
        "completeness": float 0-1,
        "reasoning": str
      }
    """
    prompt = f"""Evaluate answer quality.

Question:
{question}

Answer:
{answer}

{("Expected answer (reference):\\n" + expected) if expected else ""}

Score:
- correctness: factual correctness vs expected/reference (or best-effort vs question if no expected)
- completeness: covers main points the user needs

Return JSON only:
{{"correctness": 0.0-1.0, "completeness": 0.0-1.0, "reasoning": "short"}}
"""
    data = _llm_json(prompt)
    if not data:
        return {"available": False, "correctness": None, "completeness": None, "reasoning": "judge_unavailable"}
    return {
        "available": True,
        "correctness": float(data.get("correctness", 0.0) or 0.0),
        "completeness": float(data.get("completeness", 0.0) or 0.0),
        "reasoning": str(data.get("reasoning") or ""),
    }


def score_retrieval_quality(*, question: str, context: str) -> Dict[str, Any]:
    """
    Returns:
      {
        "relevance": float 0-1,
        "sufficiency": float 0-1,
        "reasoning": str
      }
    """
    prompt = f"""Evaluate retrieved context quality for answering the question.

Question:
{question}

Retrieved context:
{context}

Scores:
- relevance: is the retrieved context about the question?
- sufficiency: is it sufficient to answer without guessing?

Return JSON only:
{{"relevance": 0.0-1.0, "sufficiency": 0.0-1.0, "reasoning": "short"}}
"""
    data = _llm_json(prompt)
    if not data:
        return {"available": False, "relevance": None, "sufficiency": None, "reasoning": "judge_unavailable"}
    return {
        "available": True,
        "relevance": float(data.get("relevance", 0.0) or 0.0),
        "sufficiency": float(data.get("sufficiency", 0.0) or 0.0),
        "reasoning": str(data.get("reasoning") or ""),
    }


async def run_case(client: httpx.AsyncClient, base_url: str, case: EvalCase) -> Dict[str, Any]:
    endpoint, payload = _endpoint_for(case)
    session_id = f"eval-{case.workflow}-{case.inference_mode}-{case.id}"
    payload["session_id"] = session_id

    # Call API (do not fail the whole eval run on a single request)
    t0 = time.perf_counter()
    try:
        resp = await client.post(f"{base_url}{endpoint}", json=payload, timeout=120)
        latency_ms = (time.perf_counter() - t0) * 1000.0
        data = (
            resp.json()
            if resp.headers.get("content-type", "").startswith("application/json")
            else {"raw": resp.text}
        )
    except Exception as e:
        latency_ms = (time.perf_counter() - t0) * 1000.0
        return {
            "id": case.id,
            "workflow": case.workflow,
            "pattern": case.pattern,
            "inference_mode": case.inference_mode,
            "question": case.question,
            "expected_answer": case.expected_answer,
            "endpoint": endpoint,
            "status_code": None,
            "latency_ms": latency_ms,
            "answer": "",
            "api_guardrail": None,
            "api_metadata": {},
            "error": {"type": type(e).__name__, "message": str(e)},
            "safety": {"api_blocked": None},
            "retrieval": {"k_used": None, "chunks_count": 0, "context_preview": "", "quality": {}},
            "groundedness": {"supported": None, "reason": "api_call_failed"},
            "answer_quality": {"correctness": 0.0, "completeness": 0.0, "reasoning": "api_call_failed"},
            "cost": {"relative_cost_estimate": None},
        }

    answer = str(data.get("answer") or "")
    api_guardrail = data.get("guardrail")
    api_metadata = data.get("metadata") or {}

    # Safety: rely primarily on API guardrails (fast, matches reality).
    # Optional offline guardrail checks can be enabled via EVAL_RUN_OFFLINE_GUARDRAILS=true.
    run_offline_guardrails = (os.getenv("EVAL_RUN_OFFLINE_GUARDRAILS", "false") or "false").lower() == "true"
    if run_offline_guardrails:
        try:
            gr_in = check_input_safety(case.question)
        except Exception:
            gr_in = None
        try:
            gr_out = check_output_safety(answer)
        except Exception:
            gr_out = None
    else:
        gr_in = None
        gr_out = None

    # Retrieval context (offline capture for groundedness + retrieval metrics)
    cfg = INFERENCE_CONFIGS[case.inference_mode]
    ctx_chunks = _retrieve_context(case.question, k=cfg.second_pass_k if cfg.verify_answer else cfg.base_k)
    ctx_text = "\n\n---\n\n".join(ctx_chunks[:10])

    # Groundedness (LLM verifier).
    # Note: "I don't know" is considered safe/non-hallucinatory, so treat as grounded.
    if answer.strip() == llm_factory.IDK_SENTINEL:
        grounded = {"supported": True, "reason": "idk"}
    else:
        try:
            grounded = verify_supported(question=case.question, context=ctx_text[:8000], answer=answer)
            if "supported" not in grounded:
                grounded = {"supported": None, "reason": "verifier_unavailable"}
            else:
                grounded = {"supported": bool(grounded.get("supported")), "reason": grounded.get("reason")}
        except Exception:
            grounded = {"supported": None, "reason": "verifier_unavailable"}

    # Retrieval quality
    retrieval_quality = score_retrieval_quality(question=case.question, context=ctx_text[:8000])

    # Answer quality
    answer_quality = score_answer_quality(question=case.question, answer=answer, expected=case.expected_answer)

    # Best-effort cost signals
    relative_cost = None
    if isinstance(api_metadata, dict):
        rel = (api_metadata.get("pattern_selection_estimates") or {}).get("relative_cost")
        if isinstance(rel, (int, float)):
            relative_cost = float(rel)

    return {
        "id": case.id,
        "workflow": case.workflow,
        "pattern": case.pattern,
        "inference_mode": case.inference_mode,
        "question": case.question,
        "expected_answer": case.expected_answer,
        "endpoint": endpoint,
        "status_code": resp.status_code,
        "latency_ms": latency_ms,
        "answer": answer,
        "api_guardrail": api_guardrail,
        "api_metadata": api_metadata,
        "safety": {
            "offline_input_allowed": (gr_in.allowed if gr_in is not None else None),
            "offline_input_reason": (gr_in.reason if gr_in is not None else None),
            "offline_output_allowed": (gr_out.allowed if gr_out is not None else None),
            "offline_output_reason": (gr_out.reason if gr_out is not None else None),
            "api_blocked": bool(api_guardrail.get("blocked")) if isinstance(api_guardrail, dict) else None,
        },
        "retrieval": {
            "k_used": cfg.second_pass_k if cfg.verify_answer else cfg.base_k,
            "chunks_count": len(ctx_chunks),
            "context_preview": ctx_text[:800],
            "quality": retrieval_quality,
        },
        "groundedness": grounded,
        "answer_quality": answer_quality,
        "cost": {
            "relative_cost_estimate": relative_cost,
        },
    }


def _write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=os.getenv("EVAL_API_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--dataset", default="datasets/eval_cases_local_api.jsonl")
    parser.add_argument("--out", default="eval_results/local_api_eval_results.jsonl")
    parser.add_argument("--max-concurrency", type=int, default=3)
    args = parser.parse_args()

    cases = _load_cases(Path(args.dataset))
    if not cases:
        raise SystemExit(f"No cases found in {args.dataset}")

    limits = httpx.Limits(max_connections=max(10, args.max_concurrency * 2))
    async with httpx.AsyncClient(limits=limits) as client:
        sem = asyncio.Semaphore(args.max_concurrency)

        async def _bounded(c: EvalCase):
            async with sem:
                return await run_case(client, args.base_url, c)

        results = await asyncio.gather(*[_bounded(c) for c in cases])

    _write_jsonl(Path(args.out), results)

    # Basic summary to stdout
    avg_latency = sum(r["latency_ms"] for r in results) / max(1, len(results))

    scored_quality = [r for r in results if (r.get("answer_quality") or {}).get("available") is True]
    if scored_quality:
        avg_correctness = sum(r["answer_quality"]["correctness"] for r in scored_quality) / len(scored_quality)
    else:
        avg_correctness = None

    grounded_available = [r for r in results if r.get("groundedness", {}).get("supported") is not None]
    if grounded_available:
        avg_grounded = sum(1.0 if r["groundedness"]["supported"] else 0.0 for r in grounded_available) / len(grounded_available)
    else:
        avg_grounded = None
    blocked = sum(1 for r in results if r["safety"].get("api_blocked") is True)
    print(f"✅ Wrote {len(results)} results to {args.out}")
    print(f"- avg_latency_ms: {avg_latency:.1f}")
    print(f"- avg_correctness: {avg_correctness if avg_correctness is not None else 'N/A (judge unavailable)'}")
    print(f"- grounded_rate: {avg_grounded if avg_grounded is not None else 'N/A (verifier unavailable)'}")
    print(f"- api_blocked_count: {blocked}")


if __name__ == "__main__":
    asyncio.run(main())


