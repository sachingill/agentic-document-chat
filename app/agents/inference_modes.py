from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Literal


InferenceMode = Literal["low", "balanced", "high"]


@dataclass(frozen=True)
class InferenceConfig:
    # Retrieval
    base_k: int
    second_pass_k: int
    min_chunks: int
    expansions: int

    # Verification
    verify_answer: bool


INFERENCE_CONFIGS: Dict[InferenceMode, InferenceConfig] = {
    # Low: try harder to find something, but do not loosen grounding rules.
    "low": InferenceConfig(
        base_k=8,
        second_pass_k=25,
        min_chunks=1,
        expansions=4,
        verify_answer=True,
    ),
    # Balanced: good default for production.
    "balanced": InferenceConfig(
        base_k=10,
        second_pass_k=30,
        min_chunks=2,
        expansions=4,
        verify_answer=True,
    ),
    # High: strictest; will return IDK more often unless evidence is strong.
    "high": InferenceConfig(
        base_k=12,
        second_pass_k=35,
        min_chunks=3,
        expansions=5,
        verify_answer=True,
    ),
}


