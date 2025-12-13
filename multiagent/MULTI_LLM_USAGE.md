# Multi-LLM Provider Library - Usage Guide

## Overview

The multi-agent system now supports multiple LLM providers (OpenAI, Claude, Gemini, Llama) through a unified interface. You can easily switch between providers or use different providers for different tasks.

## Quick Start

### 1. Install Required Packages

```bash
# OpenAI (usually already installed)
pip install langchain-openai

# Anthropic Claude
pip install langchain-anthropic

# Google Gemini
pip install langchain-google-genai

# Llama (via Ollama)
pip install langchain-ollama
```

### 2. Set Environment Variables

```bash
# Choose your provider(s) - set at least one API key
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
export GOOGLE_API_KEY=...

# Optional: Set default provider (default: "auto")
export LLM_PROVIDER=openai  # or "claude", "gemini", "llama", "auto"

# Optional: Ollama settings (for Llama)
export OLLAMA_BASE_URL=http://localhost:11434

# Optional: Override default models
export LLM_FAST_MODEL=gpt-4o-mini
export LLM_REASONING_MODEL=gpt-4o
export LLM_SYNTHESIS_MODEL=gpt-4o
```

Or in `.env` file:
```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...

LLM_PROVIDER=auto
LLM_FAST_MODEL=gpt-4o-mini
LLM_REASONING_MODEL=gpt-4o
LLM_SYNTHESIS_MODEL=gpt-4o
```

### 3. Use in Code

```python
from multiagent.app.models.llm_providers import create_llm, create_fast_llm, create_reasoning_llm, create_synthesis_llm

# Auto-select provider (uses first available)
llm = create_llm()

# Specify provider
llm = create_llm(provider="openai", model="gpt-4o")
llm = create_llm(provider="claude", model="claude-3-opus-20240229")
llm = create_llm(provider="gemini", model="gemini-pro")
llm = create_llm(provider="llama", model="llama3")

# Use convenience functions
fast_llm = create_fast_llm()  # For quick operations
reasoning_llm = create_reasoning_llm()  # For analysis
synthesis_llm = create_synthesis_llm()  # For final answers

# Invoke
response = llm.invoke("What is a circuit breaker?")
print(response)
```

## Provider Details

### OpenAI

**Models**:
- `gpt-4o` - Best overall performance
- `gpt-4o-mini` - Fast and cost-effective
- `gpt-4-turbo` - High quality
- `gpt-3.5-turbo` - Budget option

**Setup**:
```bash
export OPENAI_API_KEY=sk-...
```

**Usage**:
```python
llm = create_llm(provider="openai", model="gpt-4o")
```

### Anthropic Claude

**Models**:
- `claude-3-opus-20240229` - Best reasoning
- `claude-3-sonnet-20240229` - Balanced
- `claude-3-haiku-20240307` - Fast

**Setup**:
```bash
pip install langchain-anthropic
export ANTHROPIC_API_KEY=sk-ant-...
```

**Usage**:
```python
llm = create_llm(provider="claude", model="claude-3-opus-20240229")
```

### Google Gemini

**Models**:
- `gemini-pro` - Standard model
- `gemini-pro-1.5` - Latest version

**Setup**:
```bash
pip install langchain-google-genai
export GOOGLE_API_KEY=...
```

**Usage**:
```python
llm = create_llm(provider="gemini", model="gemini-pro")
```

### Llama (via Ollama)

**Models**:
- `llama3` - Latest Llama 3 model
- `llama3:8b` - Llama 3 8B parameter model
- `llama3:70b` - Llama 3 70B parameter model (best quality)
- `llama2` - Llama 2 model
- `mistral` - Mistral model (also available via Ollama)

**Setup**:
```bash
# Install Ollama
# macOS/Linux: curl -fsSL https://ollama.ai/install.sh | sh
# Or download from: https://ollama.ai

# Start Ollama service
ollama serve

# Pull a model (in another terminal)
ollama pull llama3

# Install Python package
pip install langchain-ollama

# Optional: Set Ollama base URL (default: http://localhost:11434)
export OLLAMA_BASE_URL=http://localhost:11434
```

**Usage**:
```python
llm = create_llm(provider="llama", model="llama3")
llm = create_llm(provider="llama", model="llama3:70b")  # For better quality
```

**Note**: Llama runs locally via Ollama, so no API key is needed. Just make sure Ollama is running.

## Use Cases

The library provides different models for different use cases:

### Fast Operations (Research Agent)
- Quick tool selection
- Keyword extraction
- Fast decisions

```python
llm = create_fast_llm()  # Uses LLM_FAST_MODEL
```

### Reasoning (Analysis Agent)
- Complex analysis
- Key point extraction
- Relationship identification

```python
llm = create_reasoning_llm()  # Uses LLM_REASONING_MODEL
```

### Synthesis (Synthesis Agent)
- Final answer generation
- Comprehensive responses
- High-quality output

```python
llm = create_synthesis_llm()  # Uses LLM_SYNTHESIS_MODEL
```

## Configuration Examples

### Single Provider (OpenAI)
```env
OPENAI_API_KEY=sk-...
LLM_PROVIDER=openai
LLM_FAST_MODEL=gpt-4o-mini
LLM_REASONING_MODEL=gpt-4o
LLM_SYNTHESIS_MODEL=gpt-4o
```

### Single Provider (Claude)
```env
ANTHROPIC_API_KEY=sk-ant-...
LLM_PROVIDER=claude
LLM_FAST_MODEL=claude-3-haiku-20240307
LLM_REASONING_MODEL=claude-3-opus-20240229
LLM_SYNTHESIS_MODEL=claude-3-sonnet-20240229
```

### Single Provider (Llama - Local)
```env
LLM_PROVIDER=llama
OLLAMA_BASE_URL=http://localhost:11434
LLM_FAST_MODEL=llama3:8b
LLM_REASONING_MODEL=llama3:70b
LLM_SYNTHESIS_MODEL=llama3:70b
```

### Mixed Providers (Cost Optimization)
```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
LLM_PROVIDER=auto

# Use cheaper OpenAI for fast operations
LLM_FAST_MODEL=gpt-4o-mini

# Use Claude for reasoning (better at analysis)
LLM_REASONING_MODEL=claude-3-opus-20240229

# Use OpenAI for synthesis
LLM_SYNTHESIS_MODEL=gpt-4o
```

Note: For mixed providers, you'll need to specify provider in code:
```python
fast_llm = create_fast_llm(provider="openai")
reasoning_llm = create_reasoning_llm(provider="claude")
synthesis_llm = create_synthesis_llm(provider="openai")
```

## Auto Provider Selection

When `LLM_PROVIDER=auto` (default), the factory automatically selects a provider based on available API keys or services:

1. **Priority**: OpenAI > Claude > Gemini > Llama
2. **Fallback**: First available provider
3. **Llama**: Only selected if Ollama is installed and running

```python
# Automatically uses first available provider
llm = create_llm()  # provider="auto"
```

## Advanced Usage

### Custom Configuration
```python
from multiagent.app.models.llm_providers import LLMFactory

# Create with custom settings
llm = LLMFactory.create_llm(
    provider="claude",
    model="claude-3-opus-20240229",
    temperature=0.2,
    max_tokens=2000
)
```

### Streaming
```python
llm = create_llm(provider="openai")

# Stream responses
for chunk in llm.stream("Tell me a story"):
    print(chunk, end="", flush=True)
```

### Provider Information
```python
llm = create_llm(provider="claude")

# Get provider name
print(llm.provider_name)  # "claude"

# Get configuration
print(llm.get_config())
# {
#     "provider": "claude",
#     "model": "claude-3-opus-20240229",
#     "temperature": 0.1
# }
```

## Error Handling

### Missing API Key
```python
# Raises ValueError with helpful message
try:
    llm = create_llm(provider="claude")
except ValueError as e:
    print(e)  # "Anthropic API key not found..."
```

### Missing Package
```python
# Raises ImportError with installation instructions
try:
    llm = create_llm(provider="gemini")
except ImportError as e:
    print(e)  # "langchain-google-genai is not installed..."
```

### Invalid Provider
```python
# Raises ValueError
try:
    llm = create_llm(provider="invalid")
except ValueError as e:
    print(e)  # "Unknown provider: invalid..."
```

## Migration from Old Code

### Before (OpenAI only)
```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
response = llm.invoke("Hello").content
```

### After (Multi-provider)
```python
from multiagent.app.models.llm_providers import create_llm

llm = create_llm(provider="openai", model="gpt-4o", temperature=0.1)
response = llm.invoke("Hello")  # Returns string directly
```

## Best Practices

1. **Use appropriate models for each task**:
   - Fast operations: Use cheaper/faster models
   - Reasoning: Use high-quality models
   - Synthesis: Use best models for final output

2. **Set environment variables**:
   - Don't hardcode API keys
   - Use `.env` file for local development

3. **Handle errors gracefully**:
   - Check for missing API keys
   - Handle provider-specific errors
   - Implement fallbacks if needed

4. **Monitor costs**:
   - Different providers have different pricing
   - Use cheaper models for non-critical tasks
   - Monitor usage in provider dashboards

## Troubleshooting

### "No LLM provider available"
- Set at least one API key: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `GOOGLE_API_KEY`
- Or install and run Ollama for local Llama models

### "Module not found"
- Install required package: 
  - `pip install langchain-anthropic` (for Claude)
  - `pip install langchain-google-genai` (for Gemini)
  - `pip install langchain-ollama` (for Llama)

### "API key not found"
- Check environment variable is set correctly
- Verify API key is valid
- Restart your application after setting environment variables

### "Could not connect to Ollama" (Llama)
- Make sure Ollama is installed: https://ollama.ai
- Start Ollama service: `ollama serve`
- Check Ollama is running: `curl http://localhost:11434/api/tags`
- Verify model is pulled: `ollama list`
- If using remote Ollama, set `OLLAMA_BASE_URL` environment variable

## Next Steps

1. ✅ Install required packages
2. ✅ Set API keys
3. ✅ Test with different providers
4. ✅ Configure models for your use case
5. ✅ Monitor performance and costs

---

**Need Help?** Check the implementation:
- Base interface: `multiagent/app/models/llm_providers/base.py`
- Factory: `multiagent/app/models/llm_providers/factory.py`
- Providers: `multiagent/app/models/llm_providers/*_provider.py`
