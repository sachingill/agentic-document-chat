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
        
        # Get API key
        api_key = kwargs.get("api_key") or os.getenv("OPENAI_API_KEY")
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
            **{k: v for k, v in kwargs.items() if k != "api_key"}
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
            logger.error(f"❌ OpenAI invocation error: {e}")
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
