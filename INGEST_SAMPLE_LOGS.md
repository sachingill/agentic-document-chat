# Ingest Sample Error Logs

## Sample Data Created

Created `samples/sample_error_logs.json` with **55 sample error logs** covering:
- 🔐 Authentication failures (401/403) - 15 records
- 🔑 OTP issues - 10 records  
- ⬇️ Download abuse - 8 records
- ⏱️ Database timeouts (MySQL) - 10 records
- 🐌 Slow requests (>3000ms) - 12 records

## How to Ingest

### Option 1: Via UI (Easiest)

1. Navigate to **RCA Chat** page in the Streamlit UI
2. In the left column, scroll to **"Error log ingestion"**
3. Click **"Upload error log file (JSON)"**
4. Select `samples/sample_error_logs.json`
5. Click **"Ingest error log"**

### Option 2: Via API (curl)

```bash
cd /Users/sachin/nltk_data/api

# Using the wrapper payload file
curl -X POST http://localhost:8000/rca/ingest/errors \
  -H "Content-Type: application/json" \
  -d @samples/ingest_payload.json

# Or directly with the errors array
curl -X POST http://localhost:8000/rca/ingest/errors \
  -H "Content-Type: application/json" \
  -d '{"errors": '$(cat samples/sample_error_logs.json)'}'
```

### Option 3: Via Python Script (in virtual environment)

```bash
# Activate your virtual environment first
source venv/bin/activate  # or your venv path

# Run the ingest script
python3 scripts/ingest_sample_logs.py
```

### Option 4: Via Python (direct API call)

```python
import json
import requests

# Load sample logs
with open('samples/sample_error_logs.json', 'r') as f:
    errors = json.load(f)

# Ingest via API
response = requests.post(
    "http://localhost:8000/rca/ingest/errors",
    json={"errors": errors},
    timeout=120,
)

result = response.json()
print(f"Ingested {result.get('items_ingested', 0)} error logs")
```

## Verify Ingestion

After ingesting, check the KB status:

```bash
curl http://localhost:8000/agent/debug/status
```

Or use the UI:
1. Go to **Knowledge Base** page
2. Click **"KB Status"** button
3. Should show ~55+ documents in vector DB

## Test RCA Analysis

After ingestion, try:

1. **One-Click RCA**: Click any known issue button (Auth failures, OTP issues, etc.)
2. **Manual RCA**: Paste an error message like "AuthenticationError: Invalid credentials"
3. **Quick Analysis**: Use the "Quick RCA analysis" section

The RCA system should now find similar errors and provide detailed analysis!

