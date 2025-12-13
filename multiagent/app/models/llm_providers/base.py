"""
Base LLM Provider Interface

Defines the common interface that all LLM providers must implement.
"""

from abc import ABC, abstractmethod
from typing import Iterator, Optional, Dict, Any


class BaseLLMProvider(ABC):
    """
    Base interface for all LLM providers.
    
    All providers (OpenAI, Claude, Gemini) must implement this interface
    to ensure consistent behavior across different providers.
    """
    
    def __init__(self, model: str, temperature: float = 0.1, **kwargs):
        """
        Initialize the LLM provider.
        
        Args:
            model: Model name (provider-specific)
            temperature: Temperature for generation (0.0-1.0)
            **kwargs: Additional provider-specific arguments
        """
        self.model = model
        self.temperature = temperature
        self.kwargs = kwargs
    
    @abstractmethod
    def invoke(self, prompt: str) -> str:
        """
        Invoke the LLM with a prompt and return the response.
        
        Args:
            prompt: Input prompt text
            
        Returns:
            Generated response text
        """
        pass
    
    @abstractmethod
    def stream(self, prompt: str) -> Iterator[str]:
        """
        Stream responses from the LLM.
        
        Args:
            prompt: Input prompt text
            
        Yields:
            Response chunks as they are generated
        """
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """
        Return the provider name (e.g., "openai", "claude", "gemini").
        
        Returns:
            Provider name string
        """
        pass
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get the current configuration of the LLM provider.
        
        Returns:
            Dictionary with configuration details
        """
        return {
            "provider": self.provider_name,
            "model": self.model,
            "temperature": self.temperature,
            **self.kwargs
        }
    
    def __repr__(self) -> str:
        """String representation of the provider."""
        return f"{self.provider_name}(model={self.model}, temperature={self.temperature})"
