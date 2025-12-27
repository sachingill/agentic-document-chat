# One-Click RCA for Known Issues

## Overview

The One-Click RCA feature provides instant root cause analysis for common, predefined error patterns. Instead of manually entering error messages, users can click a button to analyze known issue types.

## Features

- **Predefined Templates**: Common error patterns configured as templates
- **One-Click Analysis**: Instant RCA with a single click
- **Metadata Filtering**: Supports filtering by status codes, endpoints, latency, etc.
- **Extensible**: Easy to add new known issue templates

## Predefined Known Issues

### 1. Authentication Failures 🔐
- **Pattern**: `status=401 OR status=403`
- **Search Type**: Metadata
- **Filters**: HTTP status codes 401 or 403
- **Keywords**: authentication, authorization, unauthorized, forbidden

### 2. OTP Issues 🔑
- **Pattern**: `keyword: otp`
- **Search Type**: Keyword
- **Keywords**: otp, one-time password, verification code, 2fa

### 3. Download Abuse ⬇️
- **Pattern**: `endpoint contains /api/download/file`
- **Search Type**: Metadata
- **Filters**: Endpoint pattern matching
- **Keywords**: download, file, abuse, rate limit

### 4. Database Timeouts ⏱️
- **Pattern**: `timeout + mysql`
- **Search Type**: Semantic
- **Keywords**: timeout, mysql, database, connection, query timeout

### 5. Slow Requests 🐌
- **Pattern**: `latency_ms > 3000`
- **Search Type**: Metadata
- **Filters**: Latency comparison (> 3000ms)
- **Keywords**: slow, latency, performance, timeout

## Usage

### Via UI

1. Navigate to **RCA Chat** page
2. Scroll to **"⚡ One-Click RCA for Known Issues"** section
3. Click on any known issue card/button
4. RCA analysis runs automatically
5. Results appear in the chat with:
   - Root cause analysis
   - Recommendations
   - Insights
   - Citations

### Via API

**Get all known issues:**
```bash
curl http://localhost:8000/rca/known-issues
```

**Perform quick RCA:**
```bash
curl -X POST http://localhost:8000/rca/quick/auth_failures \
  -H "X-Tenant-ID: tenant_id"
```

## Adding New Known Issues

Edit `app/core/known_issues.py` and add a new entry to `KNOWN_ISSUES`:

```python
{
    "id": "custom_issue",
    "name": "Custom Issue Name",
    "description": "Description of the issue",
    "icon": "🔍",
    "query": "search query",
    "search_type": "metadata",  # metadata, keyword, semantic
    "search_params": {
        "key": "status",
        "values": ["500"],
    },
    "keywords": ["error", "server", "500"],
}
```

### Search Types

1. **metadata**: Filter by metadata fields (status, endpoint, latency_ms, etc.)
2. **keyword**: Exact keyword matching in error text
3. **semantic**: Semantic similarity search

### Metadata Filter Examples

**Status codes (OR):**
```python
"search_params": {
    "key": "status",
    "values": ["401", "403"],
}
```

**Pattern matching:**
```python
"search_params": {
    "key": "endpoint",
    "pattern": "/api/download/file",
}
```

**Comparison operators:**
```python
"search_params": {
    "key": "latency_ms",
    "operator": ">",
    "value": 3000,
}
```

## How It Works

1. **Template Selection**: User clicks a known issue template
2. **Query Building**: System builds search query from template
3. **Metadata Filtering**: Applies metadata filters if configured
4. **Error Retrieval**: Searches vector DB for matching errors
5. **RCA Analysis**: Runs comprehensive RCA on retrieved errors
6. **Results Display**: Shows analysis with recommendations and insights

## Configuration

Known issues are defined in `app/core/known_issues.py`. The system:
- Loads templates at startup
- Exposes via `/rca/known-issues` endpoint
- Supports dynamic filtering based on metadata
- Integrates with existing RCA analysis pipeline

## Benefits

- **Speed**: Instant analysis without manual query entry
- **Consistency**: Standardized analysis for common issues
- **Efficiency**: Reduces time to identify root causes
- **Accessibility**: Non-technical users can analyze common errors

