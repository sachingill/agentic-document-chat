"""
Google Gemini LLM Provider

Implementation of BaseLLMProvider for Google Gemini models.
"""

import os
from typing import Iterator
from langsmith import traceable
import logging

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    ChatGoogleGenerativeAI = None

from .base import BaseLLMProvider

logger = logging.getLogger(__name__)


class GeminiProvider(BaseLLMProvider):
    """Google Gemini LLM provider implementation."""
    
    def __init__(self, model: str = "gemini-pro", temperature: float = 0.1, **kwargs):
        """
        Initialize Gemini provider.
        
        Args:
            model: Gemini model name (e.g., "gemini-pro", "gemini-pro-1.5")
            temperature: Temperature for generation
            **kwargs: Additional arguments for ChatGoogleGenerativeAI
        """
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "langchain-google-genai is not installed. "
                "Install it with: pip install langchain-google-genai"
            )
        
        super().__init__(model, temperature, **kwargs)
        
        # Get API key
        api_key = kwargs.get("api_key") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "Google API key not found. "
                "Please set GOOGLE_API_KEY environment variable or pass api_key parameter."
            )
        
        # Create ChatGoogleGenerativeAI instance
        self.llm = ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            google_api_key=api_key,
            **{k: v for k, v in kwargs.items() if k not in ["api_key", "google_api_key"]}
        )
        
        logger.info(f"✅ Gemini provider initialized: {model}")
    
    @traceable(name="gemini_invoke", run_type="llm")
    def invoke(self, prompt: str) -> str:
        """
        Invoke Gemini model with a prompt.
        
        Args:
            prompt: Input prompt text
            
        Returns:
            Generated response text
        """
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            logger.error(f"❌ Gemini invocation error: {e}")
            raise
    
    def stream(self, prompt: str) -> Iterator[str]:
        """
        Stream responses from Gemini model.
        
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
            logger.error(f"❌ Gemini streaming error: {e}")
            raise
    
    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "gemini"
