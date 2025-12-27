#!/usr/bin/env python3
"""
Script to ingest sample error logs into the RCA system.
Uses the API client directly (no external dependencies).
"""

import json
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

API_URL = os.getenv("API_URL", "http://localhost:8000")
TENANT_ID = os.getenv("TENANT_ID", "default")


def ingest_sample_logs():
    """Load and ingest sample error logs using direct API call."""
    # Load sample logs
    sample_file = project_root / "samples" / "sample_error_logs.json"
    
    if not sample_file.exists():
        print(f"Error: Sample file not found at {sample_file}")
        return False
    
    with open(sample_file, "r") as f:
        errors = json.load(f)
    
    print(f"Loaded {len(errors)} error logs from {sample_file}")
    
    # Use the API directly
    try:
        from app.models.embeddings import ingest_documents
        from datetime import datetime
        
        texts = []
        metadatas = []
        
        for error in errors:
            error_msg = error.get("message", "")
            stack_trace = error.get("stack_trace", "")
            timestamp = error.get("timestamp")
            source = error.get("source", "unknown")
            metadata = error.get("metadata", {})
            
            # Combine message + stack trace for ingestion
            full_text = error_msg
            if stack_trace:
                full_text = f"{error_msg}\n\nStack Trace:\n{stack_trace}"
            
            texts.append(full_text)
            
            # Build metadata
            meta = {
                "type": "error_log",
                "source": source,
                "timestamp": timestamp or datetime.now().isoformat(),
                **metadata,
            }
            metadatas.append(meta)
        
        print(f"Ingesting {len(texts)} error logs...")
        ingest_documents(texts, metadata=metadatas)
        
        print(f"✅ Successfully ingested {len(texts)} error logs")
        return True
        
    except Exception as e:
        print(f"❌ Error ingesting logs: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = ingest_sample_logs()
    sys.exit(0 if success else 1)

