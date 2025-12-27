"""
Research Agent

Specialized in gathering information from documents.
Uses retrieve_tool, keyword_search_tool, and metadata_search_tool.
"""

from typing import List, Dict, Any
from langsmith import traceable
import logging
import sys
from pathlib import Path

# Add parent directory to path to import tools
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
from app.agents.tools import retrieve_tool, keyword_search_tool, metadata_search_tool
from app.agents.inference_modes import INFERENCE_CONFIGS, InferenceMode
from app.agents.inference_utils import expand_queries

# Import LLM factory for multi-provider support
from multiagent.app.models.llm_providers import create_fast_llm

logger = logging.getLogger(__name__)

# LLM for research decisions (uses fast model, supports multiple providers)
research_llm = create_fast_llm(temperature=0.1)


@traceable(name="research_agent", run_type="chain")
def research_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Research Agent: Gathers comprehensive information from documents.
    
    Process:
    1. Analyze question to determine search strategy
    2. Use retrieve_tool for semantic search
    3. Use keyword_search_tool for specific terms (if needed)
    4. Use metadata_search_tool if metadata filtering needed
    5. Combine and deduplicate results
    
    Args:
        state: MultiAgentState with question
        
    Returns:
        Updated state with research_context
    """
    question = state.get("question", "")
    current_context = state.get("context", [])
    metadata = state.get("metadata", {}) or {}
    mode: InferenceMode = metadata.get("inference_mode", "balanced")  # type: ignore
    cfg = INFERENCE_CONFIGS.get(mode, INFERENCE_CONFIGS["balanced"])
    
    logger.info(f"🔍 Research Agent: Gathering information for: {question[:50]}...")
    
    try:
        # Step 1: Determine search strategy using LLM
        strategy_prompt = f"""
Analyze this question and determine the best search strategy.

Question: {question}

Available strategies:
1. Semantic search (retrieve_tool) - Best for general questions
2. Keyword search (keyword_search_tool) - Best for specific terms/names
3. Metadata search (metadata_search_tool) - Best for filtering by category/topic
4. Combined - Use multiple strategies

Respond with JSON:
{{
    "primary_strategy": "semantic" | "keyword" | "metadata" | "combined",
    "needs_keyword": true/false,
    "needs_metadata": true/false,
    "reasoning": "brief explanation"
}}
"""
        
        strategy_response = research_llm.invoke(strategy_prompt).strip()
        
        # Parse JSON response
        import json
        if "```json" in strategy_response:
            strategy_response = strategy_response.split("```json")[1].split("```")[0].strip()
        elif "```" in strategy_response:
            strategy_response = strategy_response.split("```")[1].split("```")[0].strip()
        
        try:
            strategy = json.loads(strategy_response)
        except json.JSONDecodeError:
            logger.warning("Failed to parse strategy, using default semantic search")
            strategy = {"primary_strategy": "semantic", "needs_keyword": False, "needs_metadata": False}
        
        # Step 2: Execute search strategy
        #
        # IMPORTANT: Always do a semantic retrieval first.
        # Reason: smaller/local models can misclassify the strategy (e.g., pick "metadata")
        # which would otherwise skip retrieval entirely and cause empty context cascades.
        all_docs = []
        tools_used = []
        
        # Always run semantic search as the baseline
        logger.info(f"Using semantic search (retrieve_tool) [baseline] mode={mode}")
        result = retrieve_tool(question, k=cfg.base_k)
        semantic_docs = result.get("results", []) or []
        all_docs.extend(semantic_docs)
        tools_used.append("retrieve_tool")
        logger.info(f"Retrieved {len(semantic_docs)} documents from semantic search")
        
        # Keyword search if needed
        if strategy.get("needs_keyword") or strategy.get("primary_strategy") == "keyword":
            logger.info("Using keyword search")
            # Extract keywords from question
            keywords = _extract_keywords(question)
            for keyword in keywords[:3]:  # Limit to 3 keywords
                result = keyword_search_tool(keyword)
                matches = result.get("matches", [])
                all_docs.extend(matches)
            tools_used.append("keyword_search_tool")
            logger.info("Keyword search complete")
        
        # Metadata search if needed
        if strategy.get("needs_metadata") or strategy.get("primary_strategy") == "metadata":
            logger.info("Attempting metadata search")
            metadata = _extract_metadata(question)
            if metadata:
                result = metadata_search_tool(metadata["key"], metadata["value"])
                matches = result.get("results", [])
                all_docs.extend(matches)
                tools_used.append("metadata_search_tool")
                logger.info(f"Found {len(matches)} documents from metadata search")
        
        # Step 3: Deduplicate results
        deduplicated_docs = _deduplicate_documents(all_docs)

        # Second-pass retrieval if evidence is thin
        if len(deduplicated_docs) < cfg.min_chunks:
            logger.info(
                f"Second-pass retrieval triggered (mode={mode}, have={len(deduplicated_docs)}, need={cfg.min_chunks})"
            )
            for q in expand_queries(question, mode=mode)[1:]:
                result2 = retrieve_tool(q, k=cfg.second_pass_k)
                more = result2.get("results", []) or []
                all_docs.extend(more)
            tools_used.append("retrieve_tool(second_pass)")
            deduplicated_docs = _deduplicate_documents(all_docs)
        
        # Step 4: Rerank documents for quality (if we have multiple docs)
        # Note: Reranking is skipped in sync context to avoid async issues
        # Reranking will be handled at the graph level if needed
        if len(deduplicated_docs) > 5:
            # Limit to top 10 before potential reranking
            deduplicated_docs = deduplicated_docs[:10]
            logger.info(f"Limited documents to top 10 for processing")
        
        # Step 5: Update state
        state["research_context"] = deduplicated_docs
        state["context"] = deduplicated_docs  # Also update main context
        state["metadata"] = state.get("metadata", {})
        state["metadata"]["research_tools_used"] = tools_used
        state["metadata"]["research_doc_count"] = len(deduplicated_docs)
        state["metadata"]["research_strategy"] = strategy.get("primary_strategy", "semantic")
        state["metadata"]["inference_mode"] = mode
        
        logger.info(f"✅ Research Agent: Collected {len(deduplicated_docs)} unique documents")
        
    except Exception as e:
        logger.error(f"❌ Research Agent error: {e}", exc_info=True)
        state["error"] = f"Research Agent error: {str(e)}"
        state["research_context"] = []
        state["context"] = []
    
    return state


def _extract_keywords(question: str) -> List[str]:
    """Extract keywords from question for keyword search."""
    prompt = f"""
Extract 2-3 meaningful keywords from this question for exact keyword search.
Focus on technical terms, proper nouns, important concepts.

Question: {question}

Respond with JSON array: ["keyword1", "keyword2"]
"""
    try:
        response = research_llm.invoke(prompt).strip()
        import json
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            response = response.split("```")[1].split("```")[0].strip()
        
        keywords = json.loads(response)
        if isinstance(keywords, list):
            return keywords[:3]
    except Exception as e:
        logger.warning(f"Failed to extract keywords: {e}")
    
    # Fallback: simple extraction
    words = question.split()
    stop_words = {"what", "how", "is", "are", "the", "a", "an", "and", "or", "but"}
    keywords = [w.lower().strip(".,!?;:") for w in words if len(w) > 4 and w.lower() not in stop_words]
    return keywords[:3]


def _extract_metadata(question: str) -> Dict[str, str]:
    """Extract metadata (key, value) from question if mentioned."""
    prompt = f"""
Extract metadata filters from this question if it mentions specific categories, topics, or metadata fields.

Question: {question}

If metadata is mentioned, respond with JSON:
{{"key": "metadata_key", "value": "metadata_value"}}

If no metadata, respond with:
{{"key": null, "value": null}}
"""
    try:
        response = research_llm.invoke(prompt).strip()
        import json
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            response = response.split("```")[1].split("```")[0].strip()
        
        result = json.loads(response)
        if result.get("key") and result.get("value"):
            return {"key": result["key"], "value": result["value"]}
    except Exception as e:
        logger.warning(f"Failed to extract metadata: {e}")
    
    return {}


def _deduplicate_documents(docs: List[str]) -> List[str]:
    """Remove duplicate documents based on content similarity."""
    seen = set()
    deduplicated = []
    for doc in docs:
        # Use first 100 characters as deduplication key
        doc_key = doc[:100].strip().lower()
        if doc_key and doc_key not in seen:
            seen.add(doc_key)
            deduplicated.append(doc)
    return deduplicated

