from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


def _get_bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "y", "on")


@dataclass(frozen=True)
class Settings:
    """
    Central place for environment-backed configuration.

    Keep this lightweight (no extra dependencies) so import order stays predictable.
    """

    # General
    env: str = os.getenv("ENV", "local")

    # LLM
    llm_backend: str = os.getenv("LLM_BACKEND", "openai")
    llm_base_url: Optional[str] = os.getenv("LLM_BASE_URL")
    llm_api_key: Optional[str] = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_OPENAI_API_KEY")

    llm_enable_fallback: bool = _get_bool("LLM_ENABLE_FALLBACK", False)
    llm_fallback_on_idk: bool = _get_bool("LLM_FALLBACK_ON_IDK", False)

    llm_main_model: str = os.getenv("LLM_MAIN_MODEL", "gpt-4o")
    llm_fast_model: str = os.getenv("LLM_FAST_MODEL", "gpt-4o-mini")
    llm_guard_model: str = os.getenv("LLM_GUARD_MODEL", "gpt-4o-mini")
    llm_summary_model: str = os.getenv("LLM_SUMMARY_MODEL", "gpt-4o-mini")

    def validate(self) -> None:
        """
        Minimal runtime validation for startup.
        - For local OpenAI-compatible backends (Ollama/vLLM), LLM_API_KEY can be a dummy string.
        - For OpenAI fallback, OPENAI_API_KEY (or LLM_OPENAI_API_KEY) must be present.
        """
        if not (self.llm_api_key and self.llm_api_key.strip()):
            raise ValueError(
                "No LLM API key found. Set LLM_API_KEY for local OpenAI-compatible backends "
                "(e.g., Ollama at http://127.0.0.1:11434/v1) or set OPENAI_API_KEY for OpenAI."
            )


