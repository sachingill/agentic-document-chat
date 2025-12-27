from fastapi import APIRouter, UploadFile, File, Request
from typing import List, Dict, Optional
from pydantic import BaseModel

from app.agents.help_guide import is_help_query, help_answer

from app.agents.doc_agent import run_document_agent_with_citations
from app.agents.guardrails import check_input_safety, check_output_safety
from app.agents.inference_modes import InferenceMode
from app.models.embeddings import ingest_documents
from app.routers.feedback import router as feedback_router


router = APIRouter()
# Mount feedback under /agent so the UI can call POST /agent/feedback
router.include_router(feedback_router, prefix="/agent")


class TextIngestRequest(BaseModel):
    texts: List[str]
    metadatas: Optional[List[Dict]] = None


#-------------------------------------------------------
# 1) Ingest (JSON)
#-------------------------------------------------------
@router.post("/agent/ingest/json")
async def ingest_texts(payload: TextIngestRequest):
    texts = payload.texts
    metadatas = payload.metadatas if payload.metadatas else [{}] * len(texts)

    ingest_documents(texts, metadata=metadatas)

    return {"status": "success", "items_ingested": len(texts)}


#-------------------------------------------------------
# 2) Ingest (JSON + Multipart files)
#-------------------------------------------------------
@router.post("/agent/ingest")
async def ingest_files(request: Request):

    texts = []
    metadatas = []
    content_type = request.headers.get("content-type", "").lower()

    # JSON ingestion
    if "application/json" in content_type:
        body = await request.json()
        payload = TextIngestRequest(**body)
        texts.extend(payload.texts)

        if payload.metadatas:
            metadatas.extend(payload.metadatas)
        else:
            metadatas.extend([{}] * len(payload.texts))

    # File ingestion
    elif "multipart/form-data" in content_type:
        form = await request.form()
        uploaded_files = form.getlist("files")

        if not uploaded_files:
            return {"error": "No files provided in multipart form"}

        for file_item in uploaded_files:
            if hasattr(file_item, "read"):
                content = (await file_item.read()).decode("utf-8", errors="ignore")
                texts.append(content)

                filename = getattr(file_item, "filename", "unknown")
                metadatas.append({"filename": filename})

    else:
        return {
            "error": "Unsupported content type",
            "hint": "Use JSON or multipart/form-data"
        }

    if not texts:
        return {
            "error": "No files or texts provided",
            "hint": "Upload files or pass raw text"
        }

    ingest_documents(texts, metadata=metadatas)
    return {"status": "success", "items_ingested": len(texts)}


#-------------------------------------------------------
# 3) CHAT API — RAG Agent With Guardrails
#-------------------------------------------------------
@router.post("/agent/chat")
async def agent_chat(payload: dict):
    """
    RAG Chat API: now includes full input + output guardrails.
    Supports both 'question' and 'message'.
    """
    from app.models.memory import Memory

    try:
        question = payload.get("question") or payload.get("message")
        session_id = payload.get("session_id", "default")
        reset_session = payload.get("reset_session", False)
        inference_mode = payload.get("inference_mode", "balanced")

        if inference_mode not in ("low", "balanced", "high"):
            inference_mode = "balanced"

        if not question:
            return {"error": "Missing 'question' or 'message'"}

        # Reset conversation memory if asked
        if reset_session:
            Memory.clear_session(session_id)

        # ------------------------------------------
        # 💡 Help / onboarding intent (non-RAG)
        # ------------------------------------------
        # Important: check this BEFORE guardrails/LLMs so "help" works even if the guard model is unavailable.
        if is_help_query(question):
            return {
                "answer": help_answer(workflow="structured"),
                "citations": [],
                "guardrail": {"stage": "none", "blocked": False, "reason": None},
                "metadata": {"inference_mode": inference_mode, "help": True},
            }

        # ------------------------------------------
        # 🔒 1) INPUT GUARDRAIL
        # ------------------------------------------
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

        # ------------------------------------------
        # 🤖 2) RUN DOCUMENT RAG AGENT
        # ------------------------------------------
        result = await run_document_agent_with_citations(session_id, question, inference_mode=inference_mode)  # type: ignore[arg-type]
        raw_answer = result.get("answer", "")
        citations = result.get("citations", [])

        # ------------------------------------------
        # 🔒 3) OUTPUT GUARDRAIL
        # ------------------------------------------
        gr_out = check_output_safety(raw_answer)

        if gr_out.allowed:
            safe_answer = gr_out.sanitized_text or raw_answer
        else:
            safe_answer = gr_out.sanitized_text or "I cannot answer that safely."

        # ------------------------------------------
        # Final response
        # ------------------------------------------
        return {
            "answer": safe_answer,
            "citations": citations,
            "guardrail": {
                "stage": "output" if not gr_out.allowed else "none",
                "blocked": not gr_out.allowed,
                "reason": gr_out.reason if not gr_out.allowed else None
            },
            "metadata": {"inference_mode": inference_mode}
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


#-------------------------------------------------------
# 4) DEBUG: Check vector DB status
#-------------------------------------------------------
@router.get("/agent/debug/status")
async def debug_status():
    """
    Diagnostic endpoint to check vector DB and retrieval status.
    """
    from app.models.embeddings import VECTOR_DB, get_retriever
    from app.agents.tools import retrieve_tool
    
    try:
        # Check vector DB
        collection = VECTOR_DB._collection
        count = collection.count()
        
        # Get sample documents
        sample = collection.get(limit=3, include=['documents', 'metadatas'])
        sample_docs = sample.get('documents', [])
        
        # Test retrieval
        test_query = "SIM provisioning retries"
        retrieval_result = retrieve_tool(test_query)
        
        return {
            "vector_db": {
                "total_documents": count,
                "sample_documents": [
                    {
                        "content": doc[:200] + "..." if len(doc) > 200 else doc,
                        "metadata": meta
                    }
                    for doc, meta in zip(
                        sample_docs[:3],
                        sample.get('metadatas', [])[:3]
                    )
                ]
            },
            "retrieval_test": {
                "query": test_query,
                "retrieved_count": retrieval_result.get("count", 0),
                "retrieved_docs": [
                    doc[:200] + "..." if len(doc) > 200 else doc
                    for doc in retrieval_result.get("results", [])[:3]
                ]
            }
        }
    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__
        }
