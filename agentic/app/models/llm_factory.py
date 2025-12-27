"""
LLM Factory (Agentic app)

Agentic server lives in `agentic/app` which is a separate Python package namespace
from the root `app/`. To keep local-serving (Ollama) support consistent, we
provide the same factory interface here.

This factory supports any OpenAI-compatible HTTP server via `base_url`:
- Ollama OpenAI-compatible endpoint: http://127.0.0.1:11434/v1

Env vars:
- LLM_BACKEND: "openai" (default) or "vllm" (meaning: OpenAI-compatible base_url)
- LLM_BASE_URL: base URL for OpenAI-compatible server (include /v1)
- LLM_API_KEY: optional; for Ollama can be any non-empty string

Models:
- LLM_MAIN_MODEL (default: gpt-4o)
- LLM_FAST_MODEL (default: gpt-4o-mini)
- LLM_GUARD_MODEL (default: gpt-4o-mini)
- LLM_SUMMARY_MODEL (default: gpt-4o-mini)
"""

from __future__ import annotations

import os
from typing import Optional

from langchain_openai import ChatOpenAI


def _backend() -> str:
    return (os.getenv("LLM_BACKEND", "openai") or "openai").lower()

def _backend_for(purpose: str) -> str:
    env_key = f"LLM_{purpose.upper()}_BACKEND"
    return (os.getenv(env_key) or _backend()).lower()


def _base_url() -> Optional[str]:
    url = os.getenv("LLM_BASE_URL")
    return url.strip() if url and url.strip() else None


def _api_key_for_backend(backend: str) -> Optional[str]:
    backend = backend.lower()
    if backend == "openai":
        key = os.getenv("LLM_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    else:
        key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    return key.strip() if key and key.strip() else None


def create_chat_llm(*, model: str, temperature: float, purpose: str = "default") -> ChatOpenAI:
    backend = _backend_for(purpose)
    api_key = _api_key_for_backend(backend)
    base_url = _base_url()

    if not api_key:
        if backend == "openai":
            raise ValueError("Missing OpenAI API key. Set OPENAI_API_KEY (or LLM_OPENAI_API_KEY).")
        raise ValueError("Missing API key. Set LLM_API_KEY (or OPENAI_API_KEY).")

    kwargs = {"model": model, "temperature": temperature, "api_key": api_key}
    if backend == "vllm":
        if not base_url:
            raise ValueError("LLM_BACKEND=vllm requires LLM_BASE_URL (e.g., http://127.0.0.1:11434/v1)")
        kwargs["base_url"] = base_url
    elif backend == "openai":
        pass
    else:
        raise ValueError(f"Unknown LLM backend: {backend}. Use 'openai' or 'vllm'.")

    return ChatOpenAI(**kwargs)


def main_llm(*, temperature: float = 0.1) -> ChatOpenAI:
    model = os.getenv("LLM_MAIN_MODEL", "gpt-4o")
    return create_chat_llm(model=model, temperature=temperature, purpose="main")


def fast_llm(*, temperature: float = 0.1) -> ChatOpenAI:
    model = os.getenv("LLM_FAST_MODEL", "gpt-4o-mini")
    return create_chat_llm(model=model, temperature=temperature, purpose="fast")


def guard_llm(*, temperature: float = 0.0) -> ChatOpenAI:
    model = os.getenv("LLM_GUARD_MODEL", "gpt-4o-mini")
    return create_chat_llm(model=model, temperature=temperature, purpose="guard")


def summary_llm(*, temperature: float = 0.1) -> ChatOpenAI:
    model = os.getenv("LLM_SUMMARY_MODEL", "gpt-4o-mini")
    return create_chat_llm(model=model, temperature=temperature, purpose="summary")


