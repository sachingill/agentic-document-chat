from typing import Any, List, Tuple, TypedDict
from langsmith import traceable
import logging

from app.models.llm_factory import fast_llm

logger = logging.getLogger(__name__)

# Light reranker — no creativity
rerank_llm = fast_llm(temperature=0.0)

class RerankDoc(TypedDict, total=False):
    text: str
    metadata: dict[str, Any]


@traceable(name="rerank", run_type="chain")
async def rerank(question: str, docs: List[Any], top_k: int = 3) -> List[RerankDoc]:
    """
    Re-ranks retrieved chunks based on relevance using an LLM.
    Returns top_k chunks (best-first), preserving metadata when provided.
    
    Uses parallel processing for better performance.
    """
    if not docs:
        logger.warning("rerank called with empty docs list")
        return []

    # Normalize inputs to {text, metadata}
    normalized: list[RerankDoc] = []
    for d in docs:
        if isinstance(d, str):
            normalized.append({"text": d, "metadata": {}})
        elif isinstance(d, dict) and isinstance(d.get("text"), str):
            normalized.append({"text": d["text"], "metadata": d.get("metadata") or {}})
        else:
            normalized.append({"text": str(d), "metadata": {}})

    logger.info(f"Reranking {len(normalized)} documents for question: {question[:50]}...")
    scored_docs: List[Tuple[RerankDoc, float]] = []
    
    # Process all documents in parallel for better performance
    import asyncio
    
    async def score_chunk(doc: RerankDoc) -> Tuple[RerankDoc, float]:
        """Score a single chunk asynchronously"""
        chunk = doc.get("text", "")
        prompt = f"""
You are a relevance scorer. Evaluate how relevant this document chunk is to the user question.
Score strictly between 0 and 1.

Question:
{question}

Document Chunk:
{chunk}

Respond with only the numeric score.
"""
        try:
            # Use ainvoke for async LLM calls
            resp = await rerank_llm.ainvoke(prompt)
            score_text = resp.content.strip()
            score = float(score_text)
            # Clamp score to [0, 1] range
            score = max(0.0, min(1.0, score))
            logger.debug(f"Chunk scored: {score:.2f} - {chunk[:50]}...")
        except Exception as e:
            logger.warning(f"Error scoring chunk: {e}, defaulting to 0.0")
            score = 0.0
        
        return (doc, score)
    
    # Score all chunks in parallel
    results = await asyncio.gather(*[score_chunk(doc) for doc in normalized])
    scored_docs = list(results)

    # Sort by score (descending)
    scored_docs.sort(key=lambda x: x[1], reverse=True)

    logger.info(f"Reranking complete. Top scores: {[f'{s:.2f}' for _, s in scored_docs[:top_k]]}")

    # Return top_k docs (without scores)
    # If we have fewer docs than top_k, return all
    result = [doc for doc, _score in scored_docs[:top_k]]
    logger.info(f"Returning {len(result)} documents after reranking")
    return result
