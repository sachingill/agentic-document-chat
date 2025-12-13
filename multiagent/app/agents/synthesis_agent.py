"""
Synthesis Agent

Specialized in combining analyzed information into final answer.
Generates comprehensive, well-structured responses.
"""

from typing import Dict, Any
from langsmith import traceable
import logging
import sys
from pathlib import Path

# Import LLM factory for multi-provider support
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from multiagent.app.models.llm_providers import create_synthesis_llm

logger = logging.getLogger(__name__)

# LLM for synthesis (needs high quality generation, supports multiple providers)
synthesis_llm = create_synthesis_llm(temperature=0.1)


@traceable(name="synthesis_agent", run_type="chain")
def synthesis_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Synthesis Agent: Combines analyzed information into final answer.
    
    Process:
    1. Read analyzed_info from Analysis Agent
    2. Review key_points and relationships
    3. Synthesize into coherent answer
    4. Ensure completeness and clarity
    5. Format appropriately
    
    Args:
        state: MultiAgentState with analyzed_info
        
    Returns:
        Updated state with final_answer
    """
    question = state.get("question", "")
    analyzed_info = state.get("analyzed_info", "")
    key_points = state.get("key_points", [])
    relationships = state.get("relationships", [])
    research_context = state.get("research_context", [])
    
    logger.info(f"✍️ Synthesis Agent: Creating final answer")
    
    # Context size management: Limit analyzed_info length
    MAX_ANALYZED_INFO_LENGTH = 3000
    if len(analyzed_info) > MAX_ANALYZED_INFO_LENGTH:
        logger.info(f"Truncating analyzed_info from {len(analyzed_info)} to {MAX_ANALYZED_INFO_LENGTH} chars")
        analyzed_info = analyzed_info[:MAX_ANALYZED_INFO_LENGTH] + "..."
    
    if not analyzed_info:
        logger.warning("No analyzed information available, using research context directly")
        if research_context:
            analyzed_info = "\n\n".join(research_context[:3])  # Use first 3 docs
        else:
            analyzed_info = "No information available."
    
    try:
        # Build synthesis prompt
        synthesis_prompt = f"""
You are a synthesis agent. Create a comprehensive, well-structured answer based on the analyzed information.

Question: {question}

Analyzed Information:
{analyzed_info}

Key Points:
{chr(10).join(f"- {point}" for point in key_points) if key_points else "None"}

Relationships:
{chr(10).join(f"- {rel}" for rel in relationships) if relationships else "None"}

Your task:
1. Synthesize the information into a clear, complete answer
2. Ensure the answer directly addresses the question
3. Use the key points and relationships to structure the answer
4. Make it easy to understand
5. Be comprehensive but concise

Provide a well-structured answer that fully addresses the question.
"""
        
        response = synthesis_llm.invoke(synthesis_prompt)
        final_answer = response.strip()
        
        # Step 2: Calculate confidence (simple heuristic)
        confidence = _calculate_confidence(analyzed_info, key_points, research_context)
        
        # Step 3: Feedback loop - if confidence is low, mark for potential refinement
        # For now, we just log it. Future: could loop back to research agent
        if confidence < 0.6:
            logger.warning(f"Low confidence ({confidence:.2f}), answer may need refinement")
            state["metadata"] = state.get("metadata", {})
            state["metadata"]["low_confidence"] = True
            state["metadata"]["confidence"] = confidence
        
        # Step 4: Update state
        state["final_answer"] = final_answer
        state["metadata"] = state.get("metadata", {})
        state["metadata"]["synthesis_confidence"] = confidence
        state["metadata"]["synthesis_answer_length"] = len(final_answer)
        
        logger.info(f"✅ Synthesis Agent: Generated answer ({len(final_answer)} chars, confidence: {confidence:.2f})")
        
    except Exception as e:
        logger.error(f"❌ Synthesis Agent error: {e}", exc_info=True)
        state["error"] = f"Synthesis Agent error: {str(e)}"
        # Fallback: use analyzed_info as answer
        state["final_answer"] = analyzed_info if analyzed_info else "Error generating answer."
    
    return state


def _calculate_confidence(analyzed_info: str, key_points: list, research_context: list) -> float:
    """
    Calculate confidence score (0.0-1.0) based on available information.
    
    Simple heuristic:
    - More key points = higher confidence
    - More research context = higher confidence
    - Longer analyzed info = higher confidence
    """
    confidence = 0.5  # Base confidence
    
    # Add points for key points (max 0.3)
    if key_points:
        confidence += min(0.3, len(key_points) * 0.1)
    
    # Add points for research context (max 0.15)
    if research_context:
        confidence += min(0.15, len(research_context) * 0.05)
    
    # Add points for analyzed info length (max 0.05)
    if len(analyzed_info) > 200:
        confidence += 0.05
    
    return min(1.0, confidence)

