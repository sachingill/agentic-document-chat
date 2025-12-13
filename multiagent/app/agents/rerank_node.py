"""
Rerank Node

Reranks documents after research agent for better quality.
"""

from typing import Dict, Any
from langsmith import traceable
import logging
import sys
from pathlib import Path

# Add parent directory to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
from app.agents.reranker import rerank

logger = logging.getLogger(__name__)


@traceable(name="rerank_node", run_type="tool")
async def rerank_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Rerank research context for better quality.
    
    Args:
        state: MultiAgentState with research_context
        
    Returns:
        Updated state with reranked research_context
    """
    question = state.get("question", "")
    research_context = state.get("research_context", [])
    
    logger.info(f"🔄 Rerank Node: Reranking {len(research_context)} documents")
    
    if not research_context:
        logger.warning("No research context to rerank")
        return state
    
    if len(research_context) <= 1:
        logger.info("Only one document, skipping reranking")
        return state
    
    try:
        # Rerank to get top 5 most relevant documents
        reranked_docs = await rerank(question, research_context, top_k=5)
        logger.info(f"Reranked {len(research_context)} documents to top {len(reranked_docs)}")
        
        # Update state
        state["research_context"] = reranked_docs
        state["context"] = reranked_docs  # Also update main context
        
    except Exception as e:
        logger.warning(f"Reranking failed: {e}, using original documents")
        # Keep original documents if reranking fails
    
    return state


