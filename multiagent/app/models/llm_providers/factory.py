"""
LLM Factory

Factory for creating LLM instances from different providers.
Supports automatic provider selection and use-case-based model selection.
"""

import os
from typing import Optional, Literal
from langsmith import traceable
import logging

from .base import BaseLLMProvider
from .openai_provider import OpenAIProvider
from .claude_provider import ClaudeProvider
from .gemini_provider import GeminiProvider
from .llama_provider import LlamaProvider

logger = logging.getLogger(__name__)

# Provider type
ProviderType = Literal["openai", "claude", "gemini", "llama", "auto"]
UseCaseType = Literal["fast", "reasoning", "synthesis", "default"]


class LLMConfig:
    """Configuration for LLM providers."""
    
    # Provider selection
    DEFAULT_PROVIDER: ProviderType = os.getenv("LLM_PROVIDER", "auto").lower()  # type: ignore
    
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    
    # Ollama settings (for Llama)
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    # Default models by provider and use case
    DEFAULT_MODELS = {
        "openai": {
            "fast": os.getenv("LLM_FAST_MODEL", "gpt-4o-mini"),
            "reasoning": os.getenv("LLM_REASONING_MODEL", "gpt-4o"),
            "synthesis": os.getenv("LLM_SYNTHESIS_MODEL", "gpt-4o"),
            "default": os.getenv("LLM_DEFAULT_MODEL", "gpt-4o"),
        },
        "claude": {
            "fast": os.getenv("LLM_FAST_MODEL", "claude-3-haiku-20240307"),
            "reasoning": os.getenv("LLM_REASONING_MODEL", "claude-3-opus-20240229"),
            "synthesis": os.getenv("LLM_SYNTHESIS_MODEL", "claude-3-sonnet-20240229"),
            "default": os.getenv("LLM_DEFAULT_MODEL", "claude-3-sonnet-20240229"),
        },
        "gemini": {
            "fast": os.getenv("LLM_FAST_MODEL", "gemini-pro"),
            "reasoning": os.getenv("LLM_REASONING_MODEL", "gemini-pro"),
            "synthesis": os.getenv("LLM_SYNTHESIS_MODEL", "gemini-pro-1.5"),
            "default": os.getenv("LLM_DEFAULT_MODEL", "gemini-pro"),
        },
        "llama": {
            "fast": os.getenv("LLM_FAST_MODEL", "llama3:8b"),
            "reasoning": os.getenv("LLM_REASONING_MODEL", "llama3:70b"),
            "synthesis": os.getenv("LLM_SYNTHESIS_MODEL", "llama3:70b"),
            "default": os.getenv("LLM_DEFAULT_MODEL", "llama3"),
        },
    }
    
    @classmethod
    def get_available_providers(cls) -> list[str]:
        """Get list of providers with available API keys or services."""
        available = []
        if cls.OPENAI_API_KEY:
            available.append("openai")
        if cls.ANTHROPIC_API_KEY:
            available.append("claude")
        if cls.GOOGLE_API_KEY:
            available.append("gemini")
        # Check if Ollama is available (try to import and check if service is running)
        try:
            from .llama_provider import OLLAMA_AVAILABLE
            if OLLAMA_AVAILABLE:
                # Note: We can't check if Ollama is actually running without making a request
                # So we just check if the package is available
                available.append("llama")
        except ImportError:
            pass
        return available
    
    @classmethod
    def auto_select_provider(cls) -> Optional[str]:
        """
        Automatically select a provider based on available API keys or services.
        Priority: OpenAI > Claude > Gemini > Llama
        """
        available = cls.get_available_providers()
        if not available:
            return None
        
        # Priority order (cloud providers first, then local)
        priority = ["openai", "claude", "gemini", "llama"]
        for provider in priority:
            if provider in available:
                return provider
        
        return available[0]  # Fallback to first available


class LLMFactory:
    """Factory for creating LLM instances from different providers."""
    
    @staticmethod
    @traceable(name="create_llm", run_type="llm")
    def create_llm(
        provider: ProviderType = "auto",
        model: Optional[str] = None,
        temperature: float = 0.1,
        use_case: UseCaseType = "default",
        **kwargs
    ) -> BaseLLMProvider:
        """
        Create an LLM instance from the specified provider.
        
        Args:
            provider: Provider name ("openai", "claude", "gemini", "llama", or "auto")
            model: Model name (if None, uses default for use_case)
            temperature: Temperature for generation (0.0-1.0)
            use_case: Use case type ("fast", "reasoning", "synthesis", "default")
            **kwargs: Additional provider-specific arguments
            
        Returns:
            BaseLLMProvider instance
            
        Raises:
            ValueError: If provider is invalid or API key is missing
            ImportError: If required package is not installed
        """
        # Auto-select provider if needed
        if provider == "auto":
            provider = LLMConfig.auto_select_provider()
            if not provider:
                raise ValueError(
                    "No LLM provider available. Please:\n"
                    "- Set at least one API key: OPENAI_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY\n"
                    "- Or install and run Ollama for local Llama models"
                )
            logger.info(f"🔧 Auto-selected provider: {provider}")
        
        # Determine model if not specified
        if model is None:
            model = LLMConfig.DEFAULT_MODELS.get(provider, {}).get(use_case, "gpt-4o")
            logger.info(f"🔧 Using default model for {use_case}: {model}")
        
        # Create provider instance
        if provider == "openai":
            return OpenAIProvider(model=model, temperature=temperature, **kwargs)
        elif provider == "claude":
            return ClaudeProvider(model=model, temperature=temperature, **kwargs)
        elif provider == "gemini":
            return GeminiProvider(model=model, temperature=temperature, **kwargs)
        elif provider == "llama":
            # Pass Ollama base URL if not in kwargs
            if "base_url" not in kwargs:
                kwargs["base_url"] = LLMConfig.OLLAMA_BASE_URL
            return LlamaProvider(model=model, temperature=temperature, **kwargs)
        else:
            raise ValueError(
                f"Unknown provider: {provider}. "
                f"Supported providers: openai, claude, gemini, llama"
            )


# Convenience functions
def create_llm(
    provider: ProviderType = "auto",
    model: Optional[str] = None,
    temperature: float = 0.1,
    use_case: UseCaseType = "default",
    **kwargs
) -> BaseLLMProvider:
    """Create an LLM instance (convenience function)."""
    return LLMFactory.create_llm(
        provider=provider,
        model=model,
        temperature=temperature,
        use_case=use_case,
        **kwargs
    )


def create_fast_llm(
    provider: ProviderType = "auto",
    model: Optional[str] = None,
    temperature: float = 0.1,
    **kwargs
) -> BaseLLMProvider:
    """Create a fast LLM for quick operations."""
    return create_llm(
        provider=provider,
        model=model,
        temperature=temperature,
        use_case="fast",
        **kwargs
    )


def create_reasoning_llm(
    provider: ProviderType = "auto",
    model: Optional[str] = None,
    temperature: float = 0.1,
    **kwargs
) -> BaseLLMProvider:
    """Create a reasoning LLM for analysis tasks."""
    return create_llm(
        provider=provider,
        model=model,
        temperature=temperature,
        use_case="reasoning",
        **kwargs
    )


def create_synthesis_llm(
    provider: ProviderType = "auto",
    model: Optional[str] = None,
    temperature: float = 0.1,
    **kwargs
) -> BaseLLMProvider:
    """Create a synthesis LLM for generating final answers."""
    return create_llm(
        provider=provider,
        model=model,
        temperature=temperature,
        use_case="synthesis",
        **kwargs
    )
