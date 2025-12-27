from __future__ import annotations

import os
from typing import Optional, Any, Dict

from fastapi import APIRouter
from pydantic import BaseModel, Field
from langsmith import Client


router = APIRouter()


class FeedbackRequest(BaseModel):
    # Identify what the user is giving feedback on
    session_id: str = Field(default="default")
    question: str
    answer: str

    # Feedback content
    score: Optional[float] = Field(default=None, description="Numeric score (e.g., 0-1 or 1-5)")
    thumbs_up: Optional[bool] = Field(default=None, description="Alternative to score")
    comment: Optional[str] = None

    # User-provided correction (gold truth for later eval)
    expected_answer: Optional[str] = None

    # Optional explicit LangSmith run_id (best if provided by client)
    run_id: Optional[str] = None


def _get_langsmith_client() -> Optional[Client]:
    api_key = os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY")
    if not api_key:
        return None
    try:
        return Client(api_key=api_key)
    except Exception:
        return None


def _find_recent_run_id(client: Client, session_id: str, question: str) -> Optional[str]:
    """
    Best-effort lookup: find the most recent run that matches session_id and question.
    This depends on our code setting metadata.session_id and metadata.question in trace config.
    """
    project_name = os.getenv("LANGCHAIN_PROJECT") or os.getenv("LANGSMITH_PROJECT") or "rag-api"

    # LangSmith filter language: use metadata fields if present.
    # We keep it simple; if filter fails, fall back to scanning recent runs.
    filter_str = f"and(eq(metadata.session_id, '{session_id}'), eq(metadata.question, '{question}'))"
    try:
        runs = list(client.list_runs(project_name=project_name, filter=filter_str, limit=10))
        if runs:
            return str(runs[0].id)
    except Exception:
        pass

    # Fallback: scan recent root runs and match in Python.
    try:
        for run in client.list_runs(project_name=project_name, is_root=True, limit=50):
            md = (run.extra or {}).get("metadata") if hasattr(run, "extra") else None
            if isinstance(md, dict) and md.get("session_id") == session_id and md.get("question") == question:
                return str(run.id)
    except Exception:
        return None

    return None


@router.post("/feedback")
async def submit_feedback(payload: FeedbackRequest) -> Dict[str, Any]:
    """
    Collect user feedback and store it in LangSmith.

    - Adds feedback to the underlying run (if run_id is found/provided)
    - Also stores correction as a dataset example in a dedicated dataset (optional)
    """
    client = _get_langsmith_client()
    if client is None:
        return {
            "status": "skipped",
            "reason": "LangSmith is not configured (set LANGSMITH_API_KEY and LANGSMITH_TRACING=true).",
        }

    run_id = payload.run_id or _find_recent_run_id(client, payload.session_id, payload.question)

    # Normalize score
    score = payload.score
    if score is None and payload.thumbs_up is not None:
        score = 1.0 if payload.thumbs_up else 0.0

    feedback_ids = []
    if run_id:
        fb = client.create_feedback(
            run_id=run_id,
            key="user_feedback",
            score=score,
            value={
                "session_id": payload.session_id,
                "question": payload.question,
                "answer": payload.answer,
            },
            comment=payload.comment,
            correction={"expected_answer": payload.expected_answer} if payload.expected_answer else None,
        )
        feedback_ids.append(str(fb.id))

    # Optionally persist corrections to a LangSmith dataset for eval (golden set)
    dataset_name = os.getenv("LANGSMITH_USER_FEEDBACK_DATASET", "rag-user-feedback")
    example_id = None
    if payload.expected_answer:
        try:
            try:
                dataset = client.create_dataset(
                    dataset_name=dataset_name,
                    description="User feedback (question/expected) collected from production UI/API",
                )
            except Exception:
                dataset = client.read_dataset(dataset_name=dataset_name)

            ex = client.create_example(
                inputs={"question": payload.question},
                outputs={"expected": payload.expected_answer},
                metadata={
                    "session_id": payload.session_id,
                    "score": score,
                    "comment": payload.comment,
                },
                dataset_id=dataset.id,
                source_run_id=run_id,
            )
            example_id = str(ex.id)
        except Exception:
            example_id = None

    return {
        "status": "ok",
        "run_id": run_id,
        "feedback_ids": feedback_ids,
        "dataset_name": dataset_name if payload.expected_answer else None,
        "example_id": example_id,
    }


