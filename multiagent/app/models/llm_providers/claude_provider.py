"""
Anthropic Claude LLM Provider

Implementation of BaseLLMProvider for Anthropic Claude models.
"""

import os
from typing import Iterator
from langsmith import traceable
import logging

try:
    from langchain_anthropic import ChatAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    ChatAnthropic = None

from .base import BaseLLMProvider

logger = logging.getLogger(__name__)


class ClaudeProvider(BaseLLMProvider):
    """Anthropic Claude LLM provider implementation."""
    
    def __init__(self, model: str = "claude-3-opus-20240229", temperature: float = 0.1, **kwargs):
        """
        Initialize Claude provider.
        
        Args:
            model: Claude model name (e.g., "claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307")
            temperature: Temperature for generation
            **kwargs: Additional arguments for ChatAnthropic
        """
        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "langchain-anthropic is not installed. "
                "Install it with: pip install langchain-anthropic"
            )
        
        super().__init__(model, temperature, **kwargs)
        
        # Get API key
        api_key = kwargs.get("api_key") or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "Anthropic API key not found. "
                "Please set ANTHROPIC_API_KEY environment variable or pass api_key parameter."
            )
        
        # Create ChatAnthropic instance
        self.llm = ChatAnthropic(
            model=model,
            temperature=temperature,
            api_key=api_key,
            **{k: v for k, v in kwargs.items() if k != "api_key"}
        )
        
        logger.info(f"✅ Claude provider initialized: {model}")
    
    @traceable(name="claude_invoke", run_type="llm")
    def invoke(self, prompt: str) -> str:
        """
        Invoke Claude model with a prompt.
        
        Args:
            prompt: Input prompt text
            
        Returns:
            Generated response text
        """
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            logger.error(f"❌ Claude invocation error: {e}")
            raise
    
    def stream(self, prompt: str) -> Iterator[str]:
        """
        Stream responses from Claude model.
        
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
            logger.error(f"❌ Claude streaming error: {e}")
            raise
    
    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "claude"
