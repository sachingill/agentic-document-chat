# Check File Ingestion Status

## API Endpoint

**GET** `/rca/check-file/{filename}`

Check if a specific log file has been ingested into the vector database.

### Example

```bash
curl "http://localhost:8000/rca/check-file/catalina.part.aa.log"
```

### Response

**If file is found:**
```json
{
  "status": "found",
  "filename": "catalina.part.aa.log",
  "document_count": 15,
  "sample_metadata": {
    "filename": "catalina.part.aa.log",
    "type": "error_log",
    "source": "catalina.part.aa",
    "timestamp": "2024-01-15T10:30:00Z"
  },
  "message": "Found 15 documents ingested from 'catalina.part.aa.log'"
}
```

**If file is not found:**
```json
{
  "status": "not_found",
  "filename": "catalina.part.aa.log",
  "document_count": 0,
  "message": "No documents found for filename 'catalina.part.aa.log'",
  "total_documents_checked": 50
}
```

## How to Upload a File

### Via UI

1. Go to **RCA Chat** page in Streamlit UI
2. In the left column, find **"Error log ingestion"**
3. Click **"Upload error log file"**
4. Select `catalina.part.aa.log`
5. Click **"Ingest error log"**
6. Wait for success message

### Via API

```bash
curl -X POST http://localhost:8000/rca/ingest/logfile \
  -F "file=@catalina.part.aa.log" \
  -F "file_type=text"
```

### Verify After Upload

```bash
curl "http://localhost:8000/rca/check-file/catalina.part.aa.log"
```

## Current Status

For `catalina.part.aa.log`:
- **Status**: ❌ Not found in vector database
- **Action needed**: Upload the file using one of the methods above

