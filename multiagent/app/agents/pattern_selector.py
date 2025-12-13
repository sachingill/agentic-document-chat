"""
Pattern Selector

Auto-selects the best multi-agent execution pattern for a given question.

Patterns:
- sequential: Research → (Rerank) → Analysis → Synthesis (default, cost-effective)
- supervisor: Supervisor plans → specialized workers → combine (best for complex/multi-part)
- parallel: run multiple approaches → evaluator picks best (best for cross-checking quality)
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Literal, Optional, Dict, Any

from multiagent.app.models.llm_providers import create_fast_llm

Pattern = Literal["sequential", "parallel", "supervisor"]
SelectorMode = Literal["heuristic", "llm"]

# Very rough “planning estimates” to support budget-aware selection.
# These are not guarantees; they’re used only for selection constraints.
_PATTERN_ESTIMATES: dict[Pattern, dict[str, float]] = {
    # Cheaper/faster baseline
    "sequential": {"relative_cost": 1.0, "relative_latency": 1.0},
    # More LLM calls + worker synthesis
    "supervisor": {"relative_cost": 1.8, "relative_latency": 1.6},
    # Multiple agent runs + evaluator
    "parallel": {"relative_cost": 2.6, "relative_latency": 2.0},
}


@dataclass(frozen=True)
class PatternSelection:
    pattern: Pattern
    reasoning: str
    mode: SelectorMode
    estimates: dict[str, float]


def select_pattern(
    question: str,
    *,
    max_relative_cost: Optional[float] = None,
    max_relative_latency: Optional[float] = None,
) -> PatternSelection:
    """
    Select a pattern for the question.

    Mode is controlled by env var:
    - MULTIAGENT_PATTERN_SELECTOR_MODE=heuristic (default)
    - MULTIAGENT_PATTERN_SELECTOR_MODE=llm

    Optional budgets:
    - max_relative_cost: constrain selection based on relative_cost estimates
    - max_relative_latency: constrain selection based on relative_latency estimates
    """
    mode = (os.getenv("MULTIAGENT_PATTERN_SELECTOR_MODE", "heuristic") or "heuristic").lower()
    if mode == "llm":
        selection = _llm_select_pattern(question)
        if selection is not None:
            return _apply_budgets(selection, max_relative_cost=max_relative_cost, max_relative_latency=max_relative_latency)
        # fall back if LLM selection fails
    selection = _heuristic_select_pattern(question)
    return _apply_budgets(selection, max_relative_cost=max_relative_cost, max_relative_latency=max_relative_latency)


def _apply_budgets(
    selection: PatternSelection,
    *,
    max_relative_cost: Optional[float],
    max_relative_latency: Optional[float],
) -> PatternSelection:
    """
    Enforce budget constraints by degrading to cheaper/faster patterns when needed.
    Degrade order: parallel -> supervisor -> sequential.
    """
    if max_relative_cost is None and max_relative_latency is None:
        return selection

    def fits(p: Pattern) -> bool:
        est = _PATTERN_ESTIMATES[p]
        if max_relative_cost is not None and est["relative_cost"] > max_relative_cost:
            return False
        if max_relative_latency is not None and est["relative_latency"] > max_relative_latency:
            return False
        return True

    chosen = selection.pattern
    if fits(chosen):
        return selection

    # Degrade to a pattern that fits
    degrade_order: list[Pattern] = ["parallel", "supervisor", "sequential"]
    for p in degrade_order:
        if fits(p):
            return PatternSelection(
                pattern=p,
                reasoning=(
                    f"{selection.reasoning} Budget constraint applied: downgraded to '{p}' "
                    f"to fit max_relative_cost={max_relative_cost}, max_relative_latency={max_relative_latency}."
                ),
                mode=selection.mode,
                estimates=_PATTERN_ESTIMATES[p],
            )

    # If nothing fits, default to sequential
    return PatternSelection(
        pattern="sequential",
        reasoning=(
            f"{selection.reasoning} Budget constraint applied: no pattern fit the budgets; defaulted to 'sequential'."
        ),
        mode=selection.mode,
        estimates=_PATTERN_ESTIMATES["sequential"],
    )


def _heuristic_select_pattern(question: str) -> PatternSelection:
    q = (question or "").strip()
    q_lower = q.lower()

    # Strong signals for supervisor pattern (multi-part, implementation-heavy)
    supervisor_signals = [
        "implement", "architecture", "design", "step by step", "end-to-end",
        "with code", "code example", "sample code", "best practices", "guide",
        "troubleshoot", "debug", "root cause", "rca", "migrate", "optimize",
    ]
    if any(s in q_lower for s in supervisor_signals):
        return PatternSelection(
            pattern="supervisor",
            reasoning="Heuristic: question looks implementation-heavy/multi-step; supervisor-workers can delegate retrieval/analysis/code synthesis.",
            mode="heuristic",
            estimates=_PATTERN_ESTIMATES["supervisor"],
        )

    # Comparison/contrast often benefits from specialized comparison + explanation workers.
    if re.search(r"\b(vs\.?|versus|compare|difference|differences|similarities|pros and cons|trade[- ]?offs?)\b", q_lower):
        # Short comparisons can be handled sequentially; longer ones benefit from supervisor.
        if len(q) > 160 or q_lower.count(" and ") >= 2:
            return PatternSelection(
                pattern="supervisor",
                reasoning="Heuristic: comparison question with higher complexity; supervisor can use comparison/explanation workers.",
                mode="heuristic",
                estimates=_PATTERN_ESTIMATES["supervisor"],
            )
        return PatternSelection(
            pattern="sequential",
            reasoning="Heuristic: comparison question but small; sequential pipeline is sufficient.",
            mode="heuristic",
            estimates=_PATTERN_ESTIMATES["sequential"],
        )

    # Signals for parallel pattern (explicit cross-checking / evaluation request)
    parallel_signals = [
        "cross-check", "double-check", "verify", "evaluate", "rank", "score", "pick best answer",
    ]
    if any(s in q_lower for s in parallel_signals):
        return PatternSelection(
            pattern="parallel",
            reasoning="Heuristic: question asks for cross-checking/evaluation; parallel competitive pattern fits.",
            mode="heuristic",
            estimates=_PATTERN_ESTIMATES["parallel"],
        )

    # Length / multi-clause heuristics
    clause_count = q.count("?") + q_lower.count(" and ") + q_lower.count(" also ") + q_lower.count(" then ")
    if len(q) > 220 or clause_count >= 3:
        return PatternSelection(
            pattern="supervisor",
            reasoning="Heuristic: long/multi-clause question; supervisor-workers can split tasks.",
            mode="heuristic",
            estimates=_PATTERN_ESTIMATES["supervisor"],
        )

    return PatternSelection(
        pattern="sequential",
        reasoning="Heuristic: straightforward question; sequential pipeline is fastest and cost-effective.",
        mode="heuristic",
        estimates=_PATTERN_ESTIMATES["sequential"],
    )


def _llm_select_pattern(question: str) -> PatternSelection | None:
    """
    LLM-based classifier. Returns None if anything goes wrong (fallback to heuristics).
    """
    try:
        llm = create_fast_llm(temperature=0.0)
        prompt = f"""
You are selecting an execution pattern for a multi-agent RAG system.

Patterns:
- sequential: best for simple/medium questions; cost-effective
- supervisor: best for complex, multi-part, implementation-heavy questions; can delegate to workers
- parallel: best when user wants cross-checking / multiple approaches and an evaluator to pick best

Question:
{question}

Respond with JSON only:
{{
  "pattern": "sequential" | "supervisor" | "parallel",
  "reasoning": "one sentence"
}}
"""
        raw = (llm.invoke(prompt) or "").strip()

        # Strip fenced blocks if present
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()

        data = json.loads(raw)
        pattern = data.get("pattern")
        reasoning = data.get("reasoning") or "LLM-selected pattern."
        if pattern not in ("sequential", "supervisor", "parallel"):
            return None
        return PatternSelection(pattern=pattern, reasoning=f"LLM: {reasoning}", mode="llm", estimates=_PATTERN_ESTIMATES[pattern])
    except Exception:
        return None


