# Log File Upload & RCA Analysis

## Overview

The RCA system now supports uploading and parsing various log file formats, automatically extracting error entries for root cause analysis.

## Supported Log Formats

### 1. **Plain Text Logs** (`.log`, `.txt`)
Standard application logs with error messages and stack traces.

**Example:**
```
2024-01-15 10:30:00 ERROR AuthenticationError: Invalid credentials provided
  File "/app/auth.py", line 45, in authenticate
    if not user.verify_password(password):
AuthenticationError: Invalid credentials provided
```

**Features:**
- Auto-detects error lines (ERROR, FATAL, EXCEPTION keywords)
- Extracts stack traces
- Parses timestamps (ISO format, common date formats)

### 2. **Syslog Format** (`.log`)
Standard syslog format: `timestamp hostname service[pid]: message`

**Example:**
```
Jan 15 10:30:00 api-server auth-service[1234]: ERROR AuthenticationError: Invalid credentials
```

**Features:**
- Parses syslog timestamp format
- Extracts hostname, service, and PID
- Detects error-level messages

### 3. **JSONL/NDJSON** (`.jsonl`, `.ndjson`)
One JSON object per line, commonly used for structured logging.

**Example:**
```jsonl
{"timestamp": "2024-01-15T10:30:00Z", "level": "ERROR", "message": "AuthenticationError: Invalid credentials", "service": "auth-service"}
{"timestamp": "2024-01-15T10:32:15Z", "level": "ERROR", "message": "ForbiddenError: Insufficient permissions", "service": "api-server"}
```

**Features:**
- Parses each line as JSON
- Extracts error-level entries
- Preserves all metadata fields

### 4. **CSV Logs** (`.csv`)
Comma-separated values with timestamp, level, and message columns.

**Example:**
```csv
timestamp,level,message,service
2024-01-15T10:30:00Z,ERROR,AuthenticationError: Invalid credentials,auth-service
2024-01-15T10:32:15Z,ERROR,ForbiddenError: Insufficient permissions,api-server
```

**Features:**
- Auto-detects column positions
- Extracts error-level rows
- Preserves additional columns as metadata

### 5. **Structured JSON** (`.json`)
Array of error objects (existing format, still supported).

**Example:**
```json
[
  {
    "message": "AuthenticationError: Invalid credentials",
    "stack_trace": "Traceback...",
    "timestamp": "2024-01-15T10:30:00Z",
    "source": "api-server"
  }
]
```

## How to Upload Log Files

### Via UI (Streamlit)

1. Navigate to **RCA Chat** page
2. In the left column, find **"Error log ingestion"**
3. Click **"Upload error log file"**
4. Select your log file (supports `.json`, `.jsonl`, `.log`, `.txt`, `.csv`)
5. Click **"Ingest error log"**
6. The system will:
   - Auto-detect the log format
   - Parse and extract error entries
   - Ingest them into the vector DB
   - Show success message with count

### Via API

**Endpoint:** `POST /rca/ingest/logfile`

**Request:**
```bash
curl -X POST http://localhost:8000/rca/ingest/logfile \
  -F "file=@/path/to/your/logfile.log" \
  -F "file_type=text"  # Optional: text, syslog, jsonl, csv, json
```

**Response:**
```json
{
  "status": "success",
  "items_ingested": 9,
  "message": "Successfully parsed and ingested 9 errors from log file",
  "file_info": {
    "filename": "sample_app.log",
    "format": "auto-detected",
    "errors_found": 9
  }
}
```

## Log Parsing Details

### Error Detection

The parser looks for:
- **Keywords**: `ERROR`, `ERR`, `FATAL`, `CRITICAL`, `EXCEPTION`, `FAILED`, `FAILURE`
- **Stack traces**: Lines starting with `Traceback`, `File`, or containing `at line`
- **Error patterns**: Common error message formats

### Metadata Extraction

For each error, the parser extracts:
- **Message**: Primary error message
- **Stack trace**: Full stack trace (if available)
- **Timestamp**: ISO format timestamp
- **Source**: Filename or service identifier
- **Additional metadata**: Service, user_id, endpoint, etc. (format-dependent)

### Auto-Detection

If `file_type` is not specified, the parser auto-detects based on:
1. **File extension**: `.jsonl` → JSONL, `.csv` → CSV, etc.
2. **Content analysis**: First line patterns (JSON, syslog, CSV)
3. **Default**: Plain text if no pattern matches

## Sample Log Files

Sample log files are available in `samples/`:
- `sample_app.log` - Plain text application log
- `sample_syslog.log` - Syslog format
- `sample_errors.jsonl` - JSONL format
- `sample_error_logs.json` - Structured JSON (existing format)

## RCA Analysis After Upload

Once logs are ingested:

1. **One-Click RCA**: Use predefined templates for common issues
2. **Manual RCA**: Paste error messages for analysis
3. **RCA Chat**: Conversational analysis with the RCA agent

The system will:
- Find similar errors from ingested logs
- Identify patterns and trends
- Provide root cause analysis
- Generate recommendations
- Show citations to similar errors

## Troubleshooting

### No Errors Found

If the parser finds no errors:
- Check that your log file contains error-level entries
- Verify keywords like `ERROR`, `FATAL`, `EXCEPTION` are present
- Try specifying `file_type` explicitly

### Parsing Errors

If parsing fails:
- Check file encoding (should be UTF-8)
- Verify file format matches expected structure
- Try a smaller sample first
- Check API logs for detailed error messages

### Large Files

For large log files (>10MB):
- Consider splitting into smaller batches
- Use JSONL format for better performance
- Process in chunks via API

## Integration Examples

### Python
```python
import requests

with open('app.log', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/rca/ingest/logfile',
        files={'file': ('app.log', f, 'application/octet-stream')},
        data={'file_type': 'text'},
        headers={'X-Tenant-ID': 'your-tenant-id'},
    )
    print(response.json())
```

### cURL
```bash
# Plain text log
curl -X POST http://localhost:8000/rca/ingest/logfile \
  -F "file=@app.log" \
  -F "file_type=text"

# JSONL log
curl -X POST http://localhost:8000/rca/ingest/logfile \
  -F "file=@errors.jsonl" \
  -F "file_type=jsonl"

# Syslog
curl -X POST http://localhost:8000/rca/ingest/logfile \
  -F "file=@syslog.log" \
  -F "file_type=syslog"
```

## Next Steps

After uploading logs:
1. ✅ Verify ingestion: Check KB status in UI
2. 🔍 Test RCA: Try one-click RCA or manual analysis
3. 📊 Review patterns: Use RCA chat to explore trends
4. 🔔 Set up alerts: Configure monitoring for critical errors

