from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.agents.agentic_flow import run_agentic
from app.agents.help_guide import is_help_query, help_answer
from app.agents.inference_modes import InferenceMode

router = APIRouter(tags=["agentic"])


class AgenticChatRequest(BaseModel):
    question: str = Field(..., min_length=1)
    session_id: str | None = None
    max_iters: int = Field(default=3, ge=1, le=6)
    inference_mode: InferenceMode = "balanced"


class AgenticChatResponse(BaseModel):
    answer: str
    metadata: dict


@router.post("/agentic/chat", response_model=AgenticChatResponse)
def agentic_chat(req: AgenticChatRequest) -> AgenticChatResponse:
    if is_help_query(req.question):
        return AgenticChatResponse(
            answer=help_answer(workflow="agentic"),
            metadata={
                "mode": "agentic-lite",
                "inference_mode": req.inference_mode,
                "help": True,
            },
        )
    result = run_agentic(req.question, max_iters=req.max_iters, inference_mode=req.inference_mode)
    return AgenticChatResponse(
        answer=result.answer,
        metadata={
            "tools_used": result.tools_used,
            "retrieved_docs_count": result.retrieved_docs_count,
            "mode": "agentic-lite",
            "inference_mode": req.inference_mode,
        },
    )


