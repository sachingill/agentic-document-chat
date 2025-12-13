"""
Analysis Agent

Specialized in analyzing and structuring gathered information.
Extracts key points, identifies relationships, and structures information logically.
"""

from typing import Dict, Any, List
from langsmith import traceable
import logging
import sys
from pathlib import Path

# Add parent directory to path to import tools
sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from app.agents.tools import summarize_tool

# Import LLM factory for multi-provider support
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from multiagent.app.models.llm_providers import create_reasoning_llm

logger = logging.getLogger(__name__)

# LLM for analysis (needs reasoning capability, supports multiple providers)
analysis_llm = create_reasoning_llm(temperature=0.1)


@traceable(name="analysis_agent", run_type="chain")
def analysis_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analysis Agent: Analyzes and structures gathered information.
    
    Process:
    1. Read research_context from Research Agent
    2. If context is too long, summarize first
    3. Extract key points
    4. Identify relationships
    5. Structure information logically
    
    Args:
        state: MultiAgentState with research_context
        
    Returns:
        Updated state with analyzed_info, key_points, relationships
    """
    question = state.get("question", "")
    research_context = state.get("research_context", [])
    
    logger.info(f"📊 Analysis Agent: Analyzing {len(research_context)} documents")
    
    if not research_context:
        logger.warning("No research context available, skipping analysis")
        state["analyzed_info"] = "No information available to analyze."
        state["key_points"] = []
        state["relationships"] = []
        return state
    
    try:
        # Step 1: Prepare context (summarize if too long)
        # Limit context size to prevent token overflow
        MAX_CONTEXT_LENGTH = 5000
        MAX_DOCS = 10
        
        # Limit number of documents
        if len(research_context) > MAX_DOCS:
            research_context = research_context[:MAX_DOCS]
            logger.info(f"Limited context to top {MAX_DOCS} documents")
        
        combined_context = "\n\n".join(research_context)
        context_length = len(combined_context)
        
        # If context is too long (>5000 chars), summarize first
        if context_length > MAX_CONTEXT_LENGTH:
            logger.info(f"Context too long ({context_length} chars), summarizing first")
            summary_result = summarize_tool(combined_context)
            summarized_context = summary_result.get("summary", combined_context)
            was_summarized = True
        else:
            summarized_context = combined_context
            was_summarized = False
        
        # Step 2: Analyze with LLM
        analysis_prompt = f"""
You are an analysis agent. Analyze the following documents and extract structured information.

Question: {question}

Documents:
{summarized_context}

Your task:
1. Extract key points relevant to the question
2. Identify important relationships between concepts
3. Structure the information logically
4. Filter out irrelevant information

Respond with JSON:
{{
    "key_points": ["point1", "point2", "point3", ...],
    "relationships": ["relationship1", "relationship2", ...],
    "structured_analysis": "Comprehensive structured analysis of the information..."
}}
"""
        
        response = analysis_llm.invoke(analysis_prompt).strip()
        
        # Parse JSON response
        import json
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            response = response.split("```")[1].split("```")[0].strip()
        
        try:
            analysis_result = json.loads(response)
            key_points = analysis_result.get("key_points", [])
            relationships = analysis_result.get("relationships", [])
            structured_analysis = analysis_result.get("structured_analysis", "")
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse analysis JSON: {e}, using fallback")
            # Fallback: simple analysis
            key_points = _extract_key_points_fallback(summarized_context)
            relationships = []
            structured_analysis = f"Analysis of {len(research_context)} documents related to: {question}"
        
        # Step 3: Update state
        state["analyzed_info"] = structured_analysis
        state["key_points"] = key_points
        state["relationships"] = relationships
        state["metadata"] = state.get("metadata", {})
        state["metadata"]["analysis_was_summarized"] = was_summarized
        state["metadata"]["analysis_key_points_count"] = len(key_points)
        state["metadata"]["analysis_relationships_count"] = len(relationships)
        
        logger.info(f"✅ Analysis Agent: Extracted {len(key_points)} key points, {len(relationships)} relationships")
        
    except Exception as e:
        logger.error(f"❌ Analysis Agent error: {e}", exc_info=True)
        state["error"] = f"Analysis Agent error: {str(e)}"
        state["analyzed_info"] = "Error during analysis."
        state["key_points"] = []
        state["relationships"] = []
    
    return state


def _extract_key_points_fallback(context: str) -> List[str]:
    """Fallback method to extract key points if LLM parsing fails."""
    # Simple extraction: split by sentences, take first few
    sentences = context.split(". ")
    return [s.strip() for s in sentences[:5] if len(s.strip()) > 20]

