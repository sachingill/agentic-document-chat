"""
AGENTIC AGENT ROUTER

This router exposes the agentic agent via FastAPI.
Key difference: Uses agentic_agent instead of structured doc_agent.
"""

from fastapi import APIRouter
import sys
import os
from pathlib import Path

# Add agentic directory to path (three levels up from router file)
# router file is at: agentic/app/routers/agentic_agent.py
# Need: agentic/ (so that "from app.xxx" imports work)
agentic_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(agentic_dir))

from app.agents.agentic_agent import run_agentic_agent
from app.agents.guardrails import check_input_safety, check_output_safety
from app.models.embeddings import ingest_documents
from typing import List, Dict, Optional
from pydantic import BaseModel

router = APIRouter()


class TextIngestRequest(BaseModel):
    texts: List[str]
    metadatas: Optional[List[Dict]] = None


#-------------------------------------------------------
# 1) Ingest (JSON) - Same as structured RAG
#-------------------------------------------------------
@router.post("/agentic/ingest/json")
async def ingest_texts(payload: TextIngestRequest):
    """Ingest documents into vector database (shared with structured RAG)"""
    texts = payload.texts
    metadatas = payload.metadatas if payload.metadatas else [{}] * len(texts)
    ingest_documents(texts, metadata=metadatas)
    return {"status": "success", "items_ingested": len(texts)}


#-------------------------------------------------------
# 2) AGENTIC CHAT API
#-------------------------------------------------------
@router.post("/agentic/chat")
async def agentic_chat(payload: dict):
    """
    AGENTIC Chat API - Uses fully agentic agent with dynamic tool selection.
    
    Key differences from structured RAG:
    - LLM decides which tools to use
    - Can loop back to refine answer
    - Dynamic routing based on agent's reasoning
    """
    from app.models.memory import Memory

    try:
        question = payload.get("question") or payload.get("message")
        session_id = payload.get("session_id", "default")
        reset_session = payload.get("reset_session", False)

        if not question:
            return {"error": "Missing 'question' or 'message'"}

        # Reset conversation memory if asked
        if reset_session:
            Memory.clear_session(session_id)

        # Input guardrail
        gr_in = check_input_safety(question)
        if not gr_in.allowed:
            return {
                "answer": "Your request was blocked by safety policies.",
                "guardrail": {
                    "stage": "input",
                    "blocked": True,
                    "reason": gr_in.reason
                }
            }

        # Run AGENTIC agent (not structured RAG)
        raw_answer = await run_agentic_agent(session_id, question)
        
        # Ensure we have a non-empty answer
        if not raw_answer or not raw_answer.strip():
            raw_answer = "I don't know based on the documents."
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("⚠️ Empty answer from agentic agent, using default")

        # Output guardrail
        gr_out = check_output_safety(raw_answer)
        if gr_out.allowed:
            safe_answer = gr_out.sanitized_text or raw_answer
        else:
            safe_answer = gr_out.sanitized_text or "I cannot answer that safely."
        
        # Final safety check
        if not safe_answer or not safe_answer.strip():
            safe_answer = "I don't know based on the documents."

        return {
            "answer": safe_answer,
            "guardrail": {
                "stage": "output" if not gr_out.allowed else "none",
                "blocked": not gr_out.allowed,
                "reason": gr_out.reason if not gr_out.allowed else None
            },
            "agentic": True  # Flag to indicate agentic flow
        }

    except ValueError as e:
        return {
            "error": "Configuration error",
            "message": str(e),
            "hint": "Check OPENAI_API_KEY in .env"
        }
    except Exception as e:
        return {
            "error": "Internal server error",
            "message": str(e),
            "type": type(e).__name__
        }

