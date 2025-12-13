"""
Llama LLM Provider

Implementation of BaseLLMProvider for Llama models via Ollama.
Ollama allows running Llama models locally or via API.
"""

import os
from typing import Iterator
from langsmith import traceable
import logging

try:
    from langchain_ollama import ChatOllama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    ChatOllama = None

from .base import BaseLLMProvider

logger = logging.getLogger(__name__)


class LlamaProvider(BaseLLMProvider):
    """Llama LLM provider implementation via Ollama."""
    
    def __init__(self, model: str = "llama3", temperature: float = 0.1, **kwargs):
        """
        Initialize Llama provider via Ollama.
        
        Args:
            model: Llama model name (e.g., "llama3", "llama3:8b", "llama3:70b", "llama2", "mistral")
            temperature: Temperature for generation
            **kwargs: Additional arguments for ChatOllama
                     - base_url: Ollama API base URL (default: http://localhost:11434)
                     - timeout: Request timeout
        """
        if not OLLAMA_AVAILABLE:
            raise ImportError(
                "langchain-ollama is not installed. "
                "Install it with: pip install langchain-ollama"
            )
        
        super().__init__(model, temperature, **kwargs)
        
        # Get Ollama base URL (default: localhost)
        base_url = kwargs.get("base_url") or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        # Create ChatOllama instance
        self.llm = ChatOllama(
            model=model,
            temperature=temperature,
            base_url=base_url,
            **{k: v for k, v in kwargs.items() if k not in ["base_url"]}
        )
        
        logger.info(f"✅ Llama provider initialized: {model} (Ollama: {base_url})")
    
    @traceable(name="llama_invoke", run_type="llm")
    def invoke(self, prompt: str) -> str:
        """
        Invoke Llama model with a prompt.
        
        Args:
            prompt: Input prompt text
            
        Returns:
            Generated response text
        """
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            logger.error(f"❌ Llama invocation error: {e}")
            # Provide helpful error message
            if "Connection" in str(e) or "refused" in str(e).lower():
                raise ConnectionError(
                    f"Could not connect to Ollama at {self.llm.base_url}. "
                    "Make sure Ollama is running. Start it with: ollama serve"
                ) from e
            raise
    
    def stream(self, prompt: str) -> Iterator[str]:
        """
        Stream responses from Llama model.
        
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
            logger.error(f"❌ Llama streaming error: {e}")
            if "Connection" in str(e) or "refused" in str(e).lower():
                raise ConnectionError(
                    f"Could not connect to Ollama at {self.llm.base_url}. "
                    "Make sure Ollama is running. Start it with: ollama serve"
                ) from e
            raise
    
    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "llama"



