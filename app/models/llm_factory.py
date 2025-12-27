"""
LLM Factory (Structured + Agentic)

This project currently uses LangChain's ChatOpenAI wrapper. vLLM can be used by
pointing ChatOpenAI at a vLLM OpenAI-compatible endpoint via `base_url`.

Env vars:
- LLM_BACKEND: "openai" (default) or "vllm"
- LLM_BASE_URL: base URL for OpenAI-compatible server (for vLLM, include /v1)
- LLM_API_KEY: optional; for vLLM can be any non-empty string

Model selection:
- LLM_MAIN_MODEL (default: gpt-4o)
- LLM_FAST_MODEL (default: gpt-4o-mini)
- LLM_GUARD_MODEL (default: gpt-4o-mini)
- LLM_SUMMARY_MODEL (default: gpt-4o-mini)
"""

from __future__ import annotations

import os
from typing import Optional

from langchain_openai import ChatOpenAI

IDK_SENTINEL = "I don't know based on the documents."

class _FallbackChatLLM:
    """
    Minimal wrapper that tries primary LLM first, then falls back to OpenAI.
    Supports `.invoke()` and `.ainvoke()` which are what we use in this repo.
    """

    def __init__(
        self,
        *,
        primary: ChatOpenAI,
        fallback: ChatOpenAI,
        fallback_on_empty: bool = True,
        fallback_on_idk: bool = False,
    ):
        self._primary = primary
        self._fallback = fallback
        self._fallback_on_empty = fallback_on_empty
        self._fallback_on_idk = fallback_on_idk

    def _should_fallback(self, text: str) -> bool:
        t = (text or "").strip()
        if self._fallback_on_empty and not t:
            return True
        if self._fallback_on_idk and t == IDK_SENTINEL:
            return True
        return False

    def invoke(self, prompt: str):
        try:
            resp = self._primary.invoke(prompt)
            content = getattr(resp, "content", str(resp))
            if self._should_fallback(content):
                return self._fallback.invoke(prompt)
            return resp
        except Exception:
            return self._fallback.invoke(prompt)

    async def ainvoke(self, prompt: str):
        try:
            resp = await self._primary.ainvoke(prompt)
            content = getattr(resp, "content", str(resp))
            if self._should_fallback(content):
                return await self._fallback.ainvoke(prompt)
            return resp
        except Exception:
            return await self._fallback.ainvoke(prompt)


def _backend() -> str:
    return (os.getenv("LLM_BACKEND", "openai") or "openai").lower()

def _backend_for(purpose: str) -> str:
    """
    Allow per-purpose override:
    - LLM_MAIN_BACKEND
    - LLM_FAST_BACKEND
    - LLM_GUARD_BACKEND
    - LLM_SUMMARY_BACKEND
    Falls back to LLM_BACKEND.
    """
    env_key = f"LLM_{purpose.upper()}_BACKEND"
    return (os.getenv(env_key) or _backend()).lower()


def _base_url() -> Optional[str]:
    url = os.getenv("LLM_BASE_URL")
    return url.strip() if url and url.strip() else None


def _api_key_for_backend(backend: str) -> Optional[str]:
    """
    API key selection:
    - For backend=openai: must use OPENAI_API_KEY (or LLM_OPENAI_API_KEY). Do NOT use LLM_API_KEY.
    - For backend=vllm (OpenAI-compatible): use LLM_API_KEY if set, else fall back to OPENAI_API_KEY.
    """
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

    # For OpenAI, api_key must exist; for vLLM, any non-empty string is fine.
    if not api_key:
        if backend == "openai":
            raise ValueError("Missing OpenAI API key. Set OPENAI_API_KEY (or LLM_OPENAI_API_KEY).")
        raise ValueError("Missing API key. Set LLM_API_KEY (or OPENAI_API_KEY).")

    kwargs = {"model": model, "temperature": temperature, "api_key": api_key}

    if backend == "vllm":
        if not base_url:
            raise ValueError("LLM_BACKEND=vllm requires LLM_BASE_URL (e.g., http://127.0.0.1:8002/v1)")
        kwargs["base_url"] = base_url
    elif backend == "openai":
        # OpenAI: do not set base_url; use standard OpenAI endpoint.
        pass
    else:
        raise ValueError(f"Unknown LLM backend: {backend}. Use 'openai' or 'vllm'.")

    return ChatOpenAI(**kwargs)

def _maybe_wrap_with_fallback(*, primary: ChatOpenAI, purpose: str) -> ChatOpenAI:
    """
    If configured, wrap a local OpenAI-compatible primary model with an OpenAI fallback.
    Enabled when:
    - LLM_ENABLE_FALLBACK=true
    and OPENAI_API_KEY (or LLM_OPENAI_API_KEY) is set.
    """
    enabled = (os.getenv("LLM_ENABLE_FALLBACK", "false") or "false").lower() == "true"
    if not enabled:
        return primary

    openai_key = os.getenv("LLM_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not openai_key:
        return primary

    # Choose fallback model by purpose
    if purpose == "fast":
        fallback_model = os.getenv("LLM_FALLBACK_FAST_MODEL", "gpt-4o-mini")
    elif purpose == "guard":
        fallback_model = os.getenv("LLM_FALLBACK_GUARD_MODEL", "gpt-4o-mini")
    else:
        fallback_model = os.getenv("LLM_FALLBACK_MAIN_MODEL", "gpt-4o")

    fallback = ChatOpenAI(model=fallback_model, temperature=getattr(primary, "temperature", 0.1), api_key=openai_key)

    fallback_on_idk = (os.getenv("LLM_FALLBACK_ON_IDK", "false") or "false").lower() == "true"
    return _FallbackChatLLM(
        primary=primary,
        fallback=fallback,
        fallback_on_empty=True,
        fallback_on_idk=fallback_on_idk,
    )

def main_llm(*, temperature: float = 0.1) -> ChatOpenAI:
    model = os.getenv("LLM_MAIN_MODEL", "gpt-4o")
    llm = create_chat_llm(model=model, temperature=temperature, purpose="main")
    return _maybe_wrap_with_fallback(primary=llm, purpose="main")


def fast_llm(*, temperature: float = 0.1) -> ChatOpenAI:
    model = os.getenv("LLM_FAST_MODEL", "gpt-4o-mini")
    llm = create_chat_llm(model=model, temperature=temperature, purpose="fast")
    return _maybe_wrap_with_fallback(primary=llm, purpose="fast")


def guard_llm(*, temperature: float = 0.0) -> ChatOpenAI:
    model = os.getenv("LLM_GUARD_MODEL", "gpt-4o-mini")
    llm = create_chat_llm(model=model, temperature=temperature, purpose="guard")
    return _maybe_wrap_with_fallback(primary=llm, purpose="guard")


def summary_llm(*, temperature: float = 0.1) -> ChatOpenAI:
    model = os.getenv("LLM_SUMMARY_MODEL", "gpt-4o-mini")
    llm = create_chat_llm(model=model, temperature=temperature, purpose="summary")
    return _maybe_wrap_with_fallback(primary=llm, purpose="summary")


