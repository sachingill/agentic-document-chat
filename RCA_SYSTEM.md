# RCA (Root Cause Analysis) Chatbot System

## Overview

The RCA chatbot is an **auto data insight generator** for application errors. It analyzes error logs, finds root causes, suggests fixes, and generates actionable insights automatically.

## Architecture

### Components

1. **RCA Tools** (`app/agents/rca_tools.py`)
   - `error_pattern_search`: Finds similar errors in ingested logs
   - `stack_trace_analyzer`: Analyzes stack traces to extract components, file paths, line numbers
   - `incident_correlator`: Finds related incidents around the same time
   - `trend_analyzer`: Analyzes error frequency trends over time
   - `root_cause_analyzer`: Comprehensive RCA combining all tools

2. **RCA Agent** (`app/agents/rca_agent.py`)
   - Orchestrates RCA workflow
   - Combines pattern search, stack analysis, correlation, trends
   - Generates natural language summary and actionable recommendations

3. **RCA Router** (`app/routers/rca.py`)
   - `POST /rca/ingest/errors`: Ingest error logs (JSON format)
   - `POST /rca/chat`: Perform RCA analysis on an error message

4. **RCA UI** (`ui.py` - RCA Chat page)
   - Error log upload (JSON files)
   - Manual error input (message + stack trace)
   - RCA chat interface
   - Displays RCA reports, recommendations, insights, citations

## Usage

### 1. Ingest Error Logs

**Via API:**
```bash
curl -X POST http://localhost:8000/rca/ingest/errors \
  -H "Content-Type: application/json" \
  -d '{
    "errors": [
      {
        "message": "ConnectionError: Failed to connect to database",
        "stack_trace": "Traceback...",
        "timestamp": "2024-01-15T10:30:00Z",
        "source": "api-server",
        "metadata": {"user_id": "123", "environment": "production"}
      }
    ]
  }'
```

**Via UI:**
- Navigate to **RCA Chat** page
- Upload JSON file or paste error details
- Click "Ingest error log"

### 2. Analyze an Error

**Via API:**
```bash
curl -X POST http://localhost:8000/rca/chat \
  -H "Content-Type: application/json" \
  -d '{
    "error_message": "ConnectionError: Failed to connect to database",
    "stack_trace": "Traceback...",
    "include_trends": true
  }'
```

**Via UI:**
- Navigate to **RCA Chat** page
- Paste error message in "Quick RCA analysis" or chat input
- Click "Analyze error" or send in chat

## Response Format

```json
{
  "summary": "Natural language summary of RCA...",
  "rca_report": {
    "root_cause": "Primary root cause explanation",
    "contributing_factors": ["factor1", "factor2"],
    "severity": "high",
    "impact": "Description of impact",
    "recommended_fixes": [
      {"action": "fix description", "priority": "high"}
    ],
    "prevention_measures": ["measure1"],
    "insights": ["insight1", "insight2"]
  },
  "pattern_analysis": {
    "similar_errors_count": 5,
    "patterns": [...]
  },
  "stack_analysis": {...},
  "correlation": {
    "correlated_incidents_count": 3,
    "incidents": [...]
  },
  "trends": {
    "total_occurrences": 12,
    "trend": "increasing",
    "average_per_day": 1.7
  },
  "recommendations": [...],
  "insights": [...],
  "citations": [...]
}
```

## Features

### Auto Data Insights

1. **Pattern Detection**: Automatically finds similar errors in historical logs
2. **Root Cause Analysis**: Uses LLM to analyze error patterns and identify root causes
3. **Trend Analysis**: Tracks error frequency over time (increasing/decreasing/stable)
4. **Correlation**: Finds related incidents that occurred around the same time
5. **Actionable Recommendations**: Provides prioritized fix suggestions
6. **Prevention Measures**: Suggests ways to prevent similar errors

### UI Features

- **Error Log Upload**: Upload JSON files with error arrays
- **Manual Input**: Paste error message + stack trace directly
- **Quick Analysis**: Fast RCA without full chat flow
- **RCA Chat**: Conversational interface for error analysis
- **Visual Reports**: Expandable RCA reports, recommendations, insights
- **Citations**: Shows similar errors found in knowledge base

## Error Log Format

```json
[
  {
    "message": "Error message text",
    "stack_trace": "Full stack trace (optional)",
    "timestamp": "2024-01-15T10:30:00Z",
    "source": "api-server",
    "metadata": {
      "user_id": "123",
      "environment": "production",
      "service": "auth-service"
    }
  }
]
```

## Integration

The RCA system integrates seamlessly with the existing RAG infrastructure:
- Uses the same vector DB (`ragdb`) for error log storage
- Leverages existing retrieval tools for pattern matching
- Uses the same LLM factory for analysis
- Follows the same guardrails for safety

## Next Steps

1. **Enhanced Error Parsing**: Support more error log formats (log4j, syslog, etc.)
2. **Alerting**: Auto-alert on critical errors or trend spikes
3. **Dashboard**: Visual dashboard for error trends and patterns
4. **Integration**: Connect with monitoring tools (Datadog, Sentry, etc.)
5. **ML Models**: Train specialized models for error classification

