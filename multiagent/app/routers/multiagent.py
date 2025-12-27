"""
Multi-Agent FastAPI Router

Provides HTTP endpoints for multi-agent RAG workflows.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Literal
import logging
import sys
import inspect
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from multiagent.app.agents.sequential_agent import run_sequential_agent
from multiagent.app.agents.parallel_agent import run_parallel_agent
from multiagent.app.agents.supervisor_workflow import run_supervisor_agent
from multiagent.app.agents.pattern_selector import select_pattern
from multiagent.app.telemetry.selection_logger import log_selection_event
from app.agents.guardrails import check_input_safety, check_output_safety
from app.agents.help_guide import is_help_query, help_answer
from app.agents.tools import retrieve_tool

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatRequest(BaseModel):
    """Request model for chat endpoints"""
    question: str
    session_id: str = "default"
    reset_session: bool = False
    # Optional override for /multiagent/chat
    # "auto" is accepted for UI convenience and treated as "no override".
    pattern: Optional[Literal["auto", "sequential", "parallel", "supervisor"]] = None
    auto_select_pattern: bool = True
    # Optional budgets for /multiagent/chat (soft constraints via relative estimates)
    # If provided, selector may downgrade pattern to fit these limits.
    max_relative_cost: Optional[float] = None
    max_relative_latency: Optional[float] = None
    # Inference strictness (affects retrieval effort + verification)
    inference_mode: Literal["low", "balanced", "high"] = "balanced"


class ChatResponse(BaseModel):
    """Response model for chat endpoints"""
    answer: str
    pattern: str
    session_id: str
    execution_time: float
    metadata: Optional[dict] = None
    error: Optional[str] = None
    guardrail: Optional[dict] = None
    citations: Optional[list[dict]] = None


def _citations_for_question(question: str, k: int = 5) -> list[dict]:
    """Lightweight citation helper: return top retrieved chunks with metadata."""
    try:
        res = retrieve_tool(question, k=k)
        docs = res.get("documents") if isinstance(res, dict) else None
        if not isinstance(docs, list):
            return []
        citations: list[dict] = []
        for d in docs[:k]:
            if not isinstance(d, dict):
                continue
            citations.append(
                {
                    "text": str(d.get("text", ""))[:500],
                    "metadata": d.get("metadata") or {},
                }
            )
        return citations
    except Exception:
        return []


@router.post("/sequential/chat", response_model=ChatResponse)
async def sequential_chat(request: ChatRequest):
    """
    Sequential Multi-Agent Chat
    
    Flow: Research Agent → Analysis Agent → Synthesis Agent
    Best for: Complex questions requiring multiple steps
    """
    try:
        # Help / onboarding intent (non-RAG)
        # Important: check this BEFORE guardrails/LLMs so "help" works even if the guard model is unavailable.
        if is_help_query(request.question):
            return ChatResponse(
                answer=help_answer(workflow="multiagent"),
                pattern="sequential",
                session_id=request.session_id,
                execution_time=0.0,
                metadata={"help": True, "mode": "multiagent"},
                citations=[],
            )

        # Input guardrail
        gr_in = check_input_safety(request.question)
        if not gr_in.allowed:
            return ChatResponse(
                answer="Your request was blocked by safety policies.",
                pattern="sequential",
                session_id=request.session_id,
                execution_time=0.0,
                guardrail={
                    "stage": "input",
                    "blocked": True,
                    "reason": gr_in.reason
                }
            )
        
        # Run sequential agent (async)
        result = await run_sequential_agent(
            question=request.question,
            session_id=request.session_id,
            inference_mode=request.inference_mode,
        )
        
        # Output guardrail
        answer = result.get("answer", "")
        gr_out = check_output_safety(answer)
        
        if not gr_out.allowed:
            safe_answer = gr_out.sanitized_text or "I cannot answer that safely."
            guardrail_info = {
                "stage": "output",
                "blocked": True,
                "reason": gr_out.reason
            }
        else:
            safe_answer = gr_out.sanitized_text or answer
            guardrail_info = None
        
        return ChatResponse(
            answer=safe_answer,
            pattern=result.get("pattern", "sequential"),
            session_id=result.get("session_id", request.session_id),
            execution_time=result.get("execution_time", 0.0),
            metadata=result.get("metadata"),
            guardrail=guardrail_info,
            citations=_citations_for_question(request.question),
        )
        
    except Exception as e:
        logger.error(f"Sequential chat error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/parallel/chat", response_model=ChatResponse)
async def parallel_chat(request: ChatRequest):
    """
    Parallel Multi-Agent Chat
    
    Flow: Multiple agents run in parallel → Evaluator selects best answer
    Best for: Comparing different approaches, ensuring best answer
    """
    try:
        # Help / onboarding intent (non-RAG)
        if is_help_query(request.question):
            return ChatResponse(
                answer=help_answer(workflow="multiagent"),
                pattern="parallel",
                session_id=request.session_id,
                execution_time=0.0,
                metadata={"help": True, "mode": "multiagent"},
                citations=[],
            )

        # Input guardrail
        gr_in = check_input_safety(request.question)
        if not gr_in.allowed:
            return ChatResponse(
                answer="Your request was blocked by safety policies.",
                pattern="parallel",
                session_id=request.session_id,
                execution_time=0.0,
                guardrail={
                    "stage": "input",
                    "blocked": True,
                    "reason": gr_in.reason
                }
            )
        
        # Run parallel agent
        result = await run_parallel_agent(
            question=request.question,
            session_id=request.session_id,
            inference_mode=request.inference_mode,
        )
        
        # Output guardrail
        answer = result.get("answer", "")
        gr_out = check_output_safety(answer)
        
        if not gr_out.allowed:
            safe_answer = gr_out.sanitized_text or "I cannot answer that safely."
            guardrail_info = {
                "stage": "output",
                "blocked": True,
                "reason": gr_out.reason
            }
        else:
            safe_answer = gr_out.sanitized_text or answer
            guardrail_info = None
        
        # Build metadata with evaluation info
        metadata = result.get("metadata", {})
        metadata.update({
            "selected_agent": result.get("selected_agent"),
            "evaluation_scores": result.get("evaluation_scores", {}),
            "evaluation_reasoning": result.get("evaluation_reasoning")
        })
        
        return ChatResponse(
            answer=safe_answer,
            pattern=result.get("pattern", "parallel"),
            session_id=result.get("session_id", request.session_id),
            execution_time=result.get("execution_time", 0.0),
            metadata=metadata,
            guardrail=guardrail_info,
            citations=_citations_for_question(request.question),
        )
        
    except Exception as e:
        logger.error(f"Parallel chat error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/supervisor/chat", response_model=ChatResponse)
async def supervisor_chat(request: ChatRequest):
    """
    Supervisor-Worker Multi-Agent Chat
    
    Flow: Supervisor delegates → Workers execute → Supervisor combines
    Best for: Complex multi-domain questions
    """
    try:
        # Help / onboarding intent (non-RAG)
        if is_help_query(request.question):
            return ChatResponse(
                answer=help_answer(workflow="multiagent"),
                pattern="supervisor",
                session_id=request.session_id,
                execution_time=0.0,
                metadata={"help": True, "mode": "multiagent"},
                citations=[],
            )

        # Input guardrail
        gr_in = check_input_safety(request.question)
        if not gr_in.allowed:
            return ChatResponse(
                answer="Your request was blocked by safety policies.",
                pattern="supervisor",
                session_id=request.session_id,
                execution_time=0.0,
                guardrail={
                    "stage": "input",
                    "blocked": True,
                    "reason": gr_in.reason
                }
            )
        
        # Run supervisor agent
        result = run_supervisor_agent(
            question=request.question,
            session_id=request.session_id,
            inference_mode=request.inference_mode,
        )
        # If the implementation is ever switched to async, handle it safely.
        if inspect.isawaitable(result):
            result = await result
        
        # Output guardrail
        answer = result.get("answer", "")
        gr_out = check_output_safety(answer)
        
        if not gr_out.allowed:
            safe_answer = gr_out.sanitized_text or "I cannot answer that safely."
            guardrail_info = {
                "stage": "output",
                "blocked": True,
                "reason": gr_out.reason
            }
        else:
            safe_answer = gr_out.sanitized_text or answer
            guardrail_info = None
        
        # Build metadata with supervisor info
        metadata = result.get("metadata", {})
        metadata.update({
            "supervisor_plan": result.get("supervisor_plan"),
            "workers_used": result.get("workers_used", [])
        })
        
        return ChatResponse(
            answer=safe_answer,
            pattern=result.get("pattern", "supervisor"),
            session_id=result.get("session_id", request.session_id),
            execution_time=result.get("execution_time", 0.0),
            metadata=metadata,
            guardrail=guardrail_info,
            citations=_citations_for_question(request.question),
        )
        
    except Exception as e:
        logger.error(f"Supervisor chat error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/chat", response_model=ChatResponse)
async def auto_select_chat(request: ChatRequest):
    """
    Auto-Select Multi-Agent Chat
    
    Automatically selects the best pattern based on question complexity.
    Supports:
    - explicit override via request.pattern
    - heuristic selection (default)
    - optional LLM selection via MULTIAGENT_PATTERN_SELECTOR_MODE=llm
    """
    # Help / onboarding intent (non-RAG)
    if is_help_query(request.question):
        return ChatResponse(
            answer=help_answer(workflow="multiagent"),
            pattern="auto",
            session_id=request.session_id,
            execution_time=0.0,
            metadata={"help": True, "mode": "multiagent"},
            citations=[],
        )

    # Safety first: do not run selector/agents if input is unsafe
    gr_in = check_input_safety(request.question)
    if not gr_in.allowed:
        return ChatResponse(
            answer="Your request was blocked by safety policies.",
            pattern="auto",
            session_id=request.session_id,
            execution_time=0.0,
            guardrail={
                "stage": "input",
                "blocked": True,
                "reason": gr_in.reason
            }
        )

    # Normalize "auto" -> no override (selector decides)
    override_pattern = request.pattern
    if override_pattern == "auto":
        override_pattern = None

    # Determine selected pattern
    if request.auto_select_pattern and override_pattern is None:
        sel = select_pattern(
            request.question,
            max_relative_cost=request.max_relative_cost,
            max_relative_latency=request.max_relative_latency,
        )
        selected_pattern = sel.pattern
        selection_reasoning = sel.reasoning
        selection_mode = sel.mode
        selection_estimates = sel.estimates
    else:
        selected_pattern = override_pattern or "sequential"
        selection_reasoning = "Manual override via request.pattern / auto_select_pattern=false."
        selection_mode = "heuristic"
        selection_estimates = {}

    # Dispatch to the chosen pattern endpoint
    if selected_pattern == "parallel":
        resp = await parallel_chat(request)
    elif selected_pattern == "supervisor":
        resp = await supervisor_chat(request)
    else:
        resp = await sequential_chat(request)

    # Attach selection info
    metadata = resp.metadata or {}
    metadata.update(
        {
            "pattern_selected": selected_pattern,
            "pattern_selection_mode": selection_mode,
            "pattern_selection_reasoning": selection_reasoning,
            "pattern_selection_estimates": selection_estimates,
            "max_relative_cost": request.max_relative_cost,
            "max_relative_latency": request.max_relative_latency,
        }
    )
    resp.metadata = metadata
    resp.pattern = selected_pattern

    # Learning-based logging (optional; JSONL)
    try:
        log_selection_event(
            {
                "session_id": request.session_id,
                "question": request.question,
                "pattern_selected": selected_pattern,
                "pattern_selection_mode": selection_mode,
                "pattern_selection_reasoning": selection_reasoning,
                "pattern_selection_estimates": selection_estimates,
                "max_relative_cost": request.max_relative_cost,
                "max_relative_latency": request.max_relative_latency,
                "execution_time": resp.execution_time,
                # quality signals when available (parallel)
                "selected_agent": (resp.metadata or {}).get("selected_agent"),
                "evaluation_scores": (resp.metadata or {}).get("evaluation_scores"),
            }
        )
    except Exception:
        # Never fail the request due to telemetry issues
        pass

    return resp



