"""
OpenAI LLM Provider

Implementation of BaseLLMProvider for OpenAI models.
"""

import os
from typing import Iterator
from langchain_openai import ChatOpenAI
from langsmith import traceable
import logging

from .base import BaseLLMProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM provider implementation."""
    
    def __init__(self, model: str = "gpt-4o", temperature: float = 0.1, **kwargs):
        """
        Initialize OpenAI provider.
        
        Args:
            model: OpenAI model name (e.g., "gpt-4o", "gpt-4o-mini", "gpt-4-turbo")
            temperature: Temperature for generation
            **kwargs: Additional arguments for ChatOpenAI
        """
        super().__init__(model, temperature, **kwargs)
        
        # Support OpenAI-compatible servers (Ollama/vLLM) via base_url env or kwargs.
        # For Ollama OpenAI-compatible API: http://127.0.0.1:11434/v1
        base_url = kwargs.get("base_url") or os.getenv("LLM_BASE_URL") or os.getenv("OPENAI_BASE_URL")
        self._base_url = base_url

        # API key selection:
        # - If using local OpenAI-compatible base_url, allow LLM_API_KEY dummy value.
        # - If calling real OpenAI (no base_url), require OPENAI_API_KEY.
        real_openai_key = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_OPENAI_API_KEY")
        api_key = kwargs.get("api_key") or (real_openai_key if not base_url else None) or os.getenv("LLM_API_KEY") or real_openai_key
        if not api_key:
            raise ValueError(
                "OpenAI API key not found. "
                "Please set OPENAI_API_KEY environment variable or pass api_key parameter."
            )
        
        # Create ChatOpenAI instance
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=api_key,
            base_url=base_url,
            **{k: v for k, v in kwargs.items() if k not in ("api_key", "base_url")}
        )
        
        logger.info(f"✅ OpenAI provider initialized: {model}")
    
    @traceable(name="openai_invoke", run_type="llm")
    def invoke(self, prompt: str) -> str:
        """
        Invoke OpenAI model with a prompt.
        
        Args:
            prompt: Input prompt text
            
        Returns:
            Generated response text
        """
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            # If we're using a local OpenAI-compatible base_url (Ollama/vLLM),
            # fall back to the real OpenAI endpoint when OPENAI_API_KEY is set.
            logger.error(f"❌ OpenAI invocation error: {e}")
            real_openai_key = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_OPENAI_API_KEY")
            has_real_openai = bool(real_openai_key)
            if self._base_url and has_real_openai:
                logger.warning("Retrying without base_url (fallback to OpenAI)")
                # If the configured model is a local-only name (e.g., "qwen2.5:3b-instruct"),
                # it will not exist on OpenAI. Map to a safe OpenAI fallback model.
                fallback_model = os.getenv("LLM_FALLBACK_MODEL")
                if not fallback_model:
                    if isinstance(self.model, str) and (self.model.startswith("gpt-") or self.model.startswith("o1") or self.model.startswith("o3")):
                        fallback_model = self.model
                    else:
                        fallback_model = "gpt-4o-mini"
                fallback_llm = ChatOpenAI(
                    model=fallback_model,
                    temperature=self.temperature,
                    api_key=real_openai_key,
                )
                response = fallback_llm.invoke(prompt)
                return response.content
            raise
    
    def stream(self, prompt: str) -> Iterator[str]:
        """
        Stream responses from OpenAI model.
        
        Args:
            prompt: Input prompt text
            
        Yields:
            Response chunks
        """
        try:
            for chunk in self.llm.stream(prompt):
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            logger.error(f"❌ OpenAI streaming error: {e}")
            raise
    
    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "openai"
