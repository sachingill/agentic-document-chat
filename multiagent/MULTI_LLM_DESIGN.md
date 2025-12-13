# Multi-LLM Provider Library - Design Document

## Overview

A custom library to support multiple LLM providers (OpenAI, Anthropic Claude, Google Gemini) with a unified interface, allowing easy switching between providers without code changes.

## Design Principles

1. **Unified Interface**: All providers implement the same interface
2. **Easy Configuration**: Environment variables for provider selection
3. **Extensible**: Easy to add new providers
4. **Type Safe**: Proper typing for all components
5. **Provider Agnostic**: Code doesn't need to know which provider is used

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              LLM Provider Abstraction                    │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   OpenAI     │  │   Claude     │  │   Gemini     │ │
│  │  Provider    │  │  Provider    │  │  Provider    │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
│         │                  │                  │         │
│         └──────────────────┼──────────────────┘         │
│                            │                            │
│                   ┌────────▼────────┐                   │
│                   │   LLM Factory   │                   │
│                   │  (Provider      │                   │
│                   │   Selector)     │                   │
│                   └────────┬────────┘                   │
│                            │                            │
│                   ┌────────▼────────┐                   │
│                   │  Unified LLM    │                   │
│                   │    Interface    │                   │
│                   └─────────────────┘                   │
└─────────────────────────────────────────────────────────┘
```

## Components

### 1. Base LLM Provider Interface

```python
class BaseLLMProvider(ABC):
    """Base interface for all LLM providers."""
    
    @abstractmethod
    def invoke(self, prompt: str) -> str:
        """Invoke the LLM with a prompt and return response."""
        pass
    
    @abstractmethod
    def stream(self, prompt: str) -> Iterator[str]:
        """Stream responses from the LLM."""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name."""
        pass
```

### 2. Provider Implementations

#### OpenAI Provider
- Uses `langchain_openai.ChatOpenAI`
- Models: `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`, etc.
- API Key: `OPENAI_API_KEY`

#### Claude Provider
- Uses `langchain_anthropic.ChatAnthropic`
- Models: `claude-3-opus`, `claude-3-sonnet`, `claude-3-haiku`
- API Key: `ANTHROPIC_API_KEY`

#### Gemini Provider
- Uses `langchain_google_genai.ChatGoogleGenerativeAI`
- Models: `gemini-pro`, `gemini-pro-1.5`
- API Key: `GOOGLE_API_KEY`

### 3. LLM Factory

```python
class LLMFactory:
    """Factory for creating LLM instances from different providers."""
    
    @staticmethod
    def create_llm(
        provider: str = "auto",  # "openai", "claude", "gemini", "auto"
        model: Optional[str] = None,
        temperature: float = 0.1,
        use_case: str = "default"
    ) -> BaseLLMProvider:
        """Create an LLM instance from the specified provider."""
        pass
```

### 4. Configuration

Environment variables:
- `LLM_PROVIDER`: `openai`, `claude`, `gemini`, or `auto` (default: `auto`)
- `OPENAI_API_KEY`: OpenAI API key
- `ANTHROPIC_API_KEY`: Anthropic API key
- `GOOGLE_API_KEY`: Google API key
- `LLM_FAST_MODEL`: Model for fast operations
- `LLM_REASONING_MODEL`: Model for reasoning tasks
- `LLM_SYNTHESIS_MODEL`: Model for synthesis tasks

## Implementation Plan

### Phase 1: Base Infrastructure
1. Create base provider interface
2. Create provider registry
3. Create factory class

### Phase 2: Provider Implementations
1. OpenAI provider
2. Claude provider
3. Gemini provider

### Phase 3: Integration
1. Update agents to use new library
2. Add configuration management
3. Add error handling and fallbacks

### Phase 4: Testing & Documentation
1. Unit tests for each provider
2. Integration tests
3. Usage documentation

## File Structure

```
multiagent/
├── app/
│   ├── models/
│   │   ├── llm_providers/
│   │   │   ├── __init__.py
│   │   │   ├── base.py          # Base provider interface
│   │   │   ├── openai_provider.py
│   │   │   ├── claude_provider.py
│   │   │   ├── gemini_provider.py
│   │   │   └── factory.py       # LLM factory
│   │   └── llm_config.py        # Configuration management
```

## Usage Example

```python
from multiagent.app.models.llm_providers import LLMFactory

# Auto-select provider based on environment
llm = LLMFactory.create_llm(
    provider="auto",  # or "openai", "claude", "gemini"
    model="gpt-4o",
    temperature=0.1
)

# Use the LLM
response = llm.invoke("What is a circuit breaker?")
print(response)
```

## Benefits

1. **No Vendor Lock-in**: Easy to switch providers
2. **Cost Optimization**: Use cheaper models for different tasks
3. **Resilience**: Fallback if one provider is down
4. **Flexibility**: Mix providers for different use cases
5. **Extensibility**: Easy to add new providers

## Next Steps

1. Review and approve design
2. Implement base infrastructure
3. Implement provider classes
4. Integrate with agents
5. Test and document
