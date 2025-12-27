"""
DEPRECATED: Agentic standalone server

We now run a single unified API (structured + multiagent + agentic) from `/app/main.py`.

This file remains as a thin compatibility shim so existing commands like:

  cd agentic && uvicorn app.main:app --port 8001

continue to work, but they will serve the unified API application.
"""

from __future__ import annotations

import importlib.util
import warnings
from pathlib import Path


warnings.warn(
    "agentic/app/main.py is deprecated. Use the unified server at app/main.py instead.",
    DeprecationWarning,
)


def _load_unified_app():
    # agentic/app/main.py -> repo_root/app/main.py
    repo_root = Path(__file__).resolve().parents[2]
    unified_main_path = repo_root / "app" / "main.py"
    if not unified_main_path.exists():
        raise RuntimeError(f"Unified app not found at: {unified_main_path}")

    spec = importlib.util.spec_from_file_location("unified_app_main", unified_main_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to create import spec for unified app")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_unified = _load_unified_app()
app = _unified.app


