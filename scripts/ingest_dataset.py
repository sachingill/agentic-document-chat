"""
Dataset Ingestion Script (High Quality)

Reads JSONL documents and ingests them via the API ingestion endpoint.

Why API-based ingestion?
- Uses the same ingestion path as production
- Keeps vector DB handling on the server

JSONL schema (one object per line):
{
  "text": "document text",
  "metadata": { ... arbitrary metadata ... }
}
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import requests


def _clean_text(text: str) -> str:
    # Normalize newlines, remove nulls, trim excessive whitespace.
    t = (text or "").replace("\x00", "")
    t = t.replace("\r\n", "\n").replace("\r", "\n")
    t = re.sub(r"[ \t]+\n", "\n", t)
    t = re.sub(r"\n{4,}", "\n\n\n", t)
    t = re.sub(r"[ \t]{2,}", " ", t)
    return t.strip()


def _stable_id(text: str) -> str:
    h = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
    return f"doc_{h}"


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                raise SystemExit(f"Invalid JSON on line {i}: {e}") from e
            if "text" not in obj:
                raise SystemExit(f"Missing 'text' on line {i}")
            if "metadata" in obj and obj["metadata"] is not None and not isinstance(obj["metadata"], dict):
                raise SystemExit(f"'metadata' must be an object on line {i}")
            items.append(obj)
    return items


def prepare(items: List[Dict[str, Any]]) -> Tuple[List[str], List[Dict[str, Any]]]:
    seen: set[str] = set()
    texts: List[str] = []
    metadatas: List[Dict[str, Any]] = []

    for obj in items:
        cleaned = _clean_text(obj.get("text", ""))
        if not cleaned:
            continue
        key = hashlib.sha256(cleaned.encode("utf-8")).hexdigest()
        if key in seen:
            continue
        seen.add(key)

        md: Dict[str, Any] = dict(obj.get("metadata") or {})
        md.setdefault("doc_id", _stable_id(cleaned))
        md.setdefault("source", "curated")

        texts.append(cleaned)
        metadatas.append(md)

    return texts, metadatas


def post_batches(api_url: str, endpoint: str, texts: List[str], metadatas: List[Dict[str, Any]], batch_size: int) -> None:
    assert len(texts) == len(metadatas)
    url = api_url.rstrip("/") + endpoint

    total = len(texts)
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        payload = {"texts": texts[start:end], "metadatas": metadatas[start:end]}
        resp = requests.post(url, json=payload, timeout=120)
        if resp.status_code >= 300:
            raise SystemExit(f"Upload failed ({resp.status_code}): {resp.text[:500]}")
        print(f"Ingested batch {start}-{end} / {total}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Path to JSONL dataset file")
    ap.add_argument("--api-url", default="http://localhost:8000", help="Base API URL")
    ap.add_argument("--endpoint", default="/agent/ingest/json", help="Ingestion endpoint")
    ap.add_argument("--batch-size", type=int, default=20, help="Docs per request")
    args = ap.parse_args()

    path = Path(args.input)
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        return 2

    items = load_jsonl(path)
    texts, metadatas = prepare(items)
    print(f"Loaded {len(items)} rows; prepared {len(texts)} unique docs after cleaning/dedupe.")

    post_batches(args.api_url, args.endpoint, texts, metadatas, args.batch_size)
    print("✅ Ingestion complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


