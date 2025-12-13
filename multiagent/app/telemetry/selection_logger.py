"""
Selection/Event Logger

Lightweight JSONL logger for learning-based tuning of pattern selection.

Controlled by env vars:
- MULTIAGENT_SELECTION_LOG_ENABLED=true|false (default: false)
- MULTIAGENT_SELECTION_LOG_PATH=/absolute/or/relative/path.jsonl (default: <project_root>/multiagent_selection_events.jsonl)
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional


def log_selection_event(event: Dict[str, Any]) -> None:
    """
    Append one JSON line to the configured log file.
    No-op unless MULTIAGENT_SELECTION_LOG_ENABLED=true.
    """
    enabled = (os.getenv("MULTIAGENT_SELECTION_LOG_ENABLED", "false") or "false").lower() == "true"
    if not enabled:
        return

    path = os.getenv("MULTIAGENT_SELECTION_LOG_PATH")
    if path:
        out_path = Path(path).expanduser()
    else:
        # project root: .../api/
        # selection_logger.py -> telemetry -> app -> multiagent -> api (project root)
        project_root = Path(__file__).resolve().parents[3]
        out_path = project_root / "multiagent_selection_events.jsonl"

    out_path.parent.mkdir(parents=True, exist_ok=True)

    payload = dict(event)
    payload.setdefault("ts", time.time())

    with out_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


