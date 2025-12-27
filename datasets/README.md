## High-quality dataset ingestion

This folder is for **curated, high-quality knowledge** that the RAG system can ingest.

### Recommended format: JSONL

Each line is a JSON object:

```json
{"text":"...document text...","metadata":{"domain":"telecom","topic":"sim_provisioning","source":"curated","doc_id":"telecom_001","title":"SIM Provisioning Overview","type":"runbook","version":"2025-12-14"}}
```

### Why this format works well

- **Rich metadata**: `domain/topic/source/doc_id` improves filtering and debugging
- **High signal text**: you can embed structure (titles, bullets, sections)
- **Easy batching**: scripts can upload 10–50 docs per request

### Ingest

Use the script:

```bash
source venv/bin/activate
python scripts/ingest_dataset.py --input datasets/high_quality_sample.jsonl --api-url http://localhost:8000
```


