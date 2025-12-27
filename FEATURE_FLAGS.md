# Feature Flags System

## Overview

The feature flags system enables **tenant-based feature configuration**, allowing different tenants to have access to different features. This is essential for multi-tenancy SaaS applications where you want to offer different feature sets to different customers.

## Architecture

### Components

1. **Feature Flags Manager** (`app/core/feature_flags.py`)
   - Loads configuration from JSON file or environment variable
   - Supports tenant-specific feature overrides
   - Provides tenant detection from HTTP requests

2. **Feature Flags Router** (`app/routers/features.py`)
   - `GET /features`: Get all features for current tenant
   - `GET /features/{feature_name}`: Check specific feature

3. **Tenant Detection**
   - Checks `X-Tenant-ID` header (primary)
   - Checks `X-API-Key` header (supports `tenant:key` format)
   - Checks `tenant` query parameter
   - Falls back to `"default"` tenant

## Configuration

### Configuration File

Create `feature_flags.json` in the project root (or set `FEATURE_FLAGS_CONFIG_PATH`):

```json
{
  "default": {
    "rca_chat": true,
    "rca_ingest": true,
    "structured_rag": true,
    "agentic_rag": true,
    "multiagent_rag": true,
    "knowledge_base": true,
    "feedback": true
  },
  "tenant_premium": {
    "rca_chat": true,
    "rca_ingest": true,
    "structured_rag": true,
    "agentic_rag": true,
    "multiagent_rag": true,
    "knowledge_base": true,
    "feedback": true
  },
  "tenant_basic": {
    "rca_chat": false,
    "rca_ingest": false,
    "structured_rag": true,
    "agentic_rag": false,
    "multiagent_rag": false,
    "knowledge_base": true,
    "feedback": true
  }
}
```

### Environment Variable

Alternatively, set `FEATURE_FLAGS_CONFIG` environment variable with JSON string:

```bash
export FEATURE_FLAGS_CONFIG='{"default":{"rca_chat":true},"tenant_basic":{"rca_chat":false}}'
```

## Usage

### API Usage

**Check features for tenant:**
```bash
curl -H "X-Tenant-ID: tenant_basic" http://localhost:8000/features
```

**Check specific feature:**
```bash
curl -H "X-Tenant-ID: tenant_basic" http://localhost:8000/features/rca_chat
```

**Use tenant-specific API:**
```bash
curl -X POST http://localhost:8000/rca/chat \
  -H "X-Tenant-ID: tenant_premium" \
  -H "Content-Type: application/json" \
  -d '{"error_message": "ConnectionError"}'
```

### In Code

**Check feature flag:**
```python
from app.core.feature_flags import is_feature_enabled, get_tenant_from_request

tenant = get_tenant_from_request(request)
if is_feature_enabled("rca_chat", tenant):
    # Feature is enabled
    pass
```

**Require feature (raises exception if disabled):**
```python
from app.core.feature_flags import require_feature

require_feature("rca_chat", tenant)  # Raises ValueError if disabled
```

**In FastAPI endpoints:**
```python
from fastapi import Request
from app.core.feature_flags import get_tenant_from_request, is_feature_enabled

@router.post("/rca/chat")
async def rca_chat(request: Request, payload: RCAChatRequest):
    tenant = get_tenant_from_request(request)
    if not is_feature_enabled("rca_chat", tenant):
        raise HTTPException(
            status_code=403,
            detail=f"RCA chat feature is not enabled for tenant '{tenant}'"
        )
    # ... rest of endpoint
```

## Available Features

- `rca_chat`: RCA chat analysis endpoint
- `rca_ingest`: RCA error log ingestion
- `structured_rag`: Structured RAG chat
- `agentic_rag`: Agentic RAG chat
- `multiagent_rag`: Multi-agent RAG workflows
- `knowledge_base`: Knowledge base ingestion and management
- `feedback`: User feedback collection

## UI Integration

The Streamlit UI automatically:
1. Loads feature flags on page load
2. Shows/hides navigation options based on flags
3. Disables features that aren't enabled
4. Shows warnings when features are disabled

**Tenant Selection:**
- Set tenant ID in sidebar
- Feature flags reload automatically
- UI adapts to show only enabled features

## Dynamic Configuration

To reload configuration without restarting:

```python
from app.core.feature_flags import get_feature_flags

flags = get_feature_flags()
flags.reload()  # Reloads from file
```

## Best Practices

1. **Default Tenant**: Always define a `"default"` tenant with safe defaults
2. **Feature Naming**: Use lowercase with underscores (e.g., `rca_chat`)
3. **Security**: Feature flags are checked server-side; UI hiding is UX only
4. **Fallback**: If tenant not found, falls back to `"default"` tenant
5. **Missing Features**: If feature not in config, defaults to `False` (safe)

## Example Tenant Tiers

**Premium Tenant** (all features):
```json
{
  "tenant_premium": {
    "rca_chat": true,
    "rca_ingest": true,
    "structured_rag": true,
    "agentic_rag": true,
    "multiagent_rag": true,
    "knowledge_base": true,
    "feedback": true
  }
}
```

**Basic Tenant** (limited features):
```json
{
  "tenant_basic": {
    "rca_chat": false,
    "rca_ingest": false,
    "structured_rag": true,
    "agentic_rag": false,
    "multiagent_rag": false,
    "knowledge_base": true,
    "feedback": true
  }
}
```

**Trial Tenant** (read-only):
```json
{
  "tenant_trial": {
    "rca_chat": true,
    "rca_ingest": false,
    "structured_rag": true,
    "agentic_rag": false,
    "multiagent_rag": false,
    "knowledge_base": true,
    "feedback": false
  }
}
```

