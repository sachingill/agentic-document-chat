"""
Sequential Multi-Agent Workflow

Pattern: Research → Analysis → Synthesis

This workflow uses specialized agents in sequence, each building on the previous agent's output.
"""

from langgraph.graph import StateGraph, END
from langsmith import traceable
import logging
import sys
from pathlib import Path

# Import agents
from .research_agent import research_agent_node
from .analysis_agent import analysis_agent_node
from .synthesis_agent import synthesis_agent_node
from .rerank_node import rerank_node

# Import state
sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from multiagent.app.models.state import MultiAgentState, finalize_state

logger = logging.getLogger(__name__)


def should_continue_sequential(state: MultiAgentState) -> str:
    """
    Determine if we should continue or skip to synthesis.
    
    Early termination: If research found sufficient info, skip analysis.
    """
    research_context = state.get("research_context", [])
    analyzed_info = state.get("analyzed_info")
    
    # If we already have analyzed info, go to synthesis
    if analyzed_info:
        return "synthesis"
    
    # Early termination: If we have good research context (>3 docs), we can skip analysis for simple questions
    # For now, always do analysis for better quality
    # Future: Add LLM check for question complexity
    return "analysis"


def build_sequential_graph():
    """
    Build the sequential multi-agent graph.
    
    Flow:
    1. Research Agent → Gathers information
    2. Rerank Node → Reranks documents for quality (optional, async)
    3. Analysis Agent → Analyzes and structures
    4. Synthesis Agent → Creates final answer
    5. END
    """
    graph = StateGraph(MultiAgentState)
    
    # Add nodes
    graph.add_node("research", research_agent_node)
    graph.add_node("rerank", rerank_node)  # Optional reranking
    graph.add_node("analysis", analysis_agent_node)
    graph.add_node("synthesis", synthesis_agent_node)
    
    # Set entry point
    graph.set_entry_point("research")
    
    # Define flow: research → rerank → analysis → synthesis → END
    # Note: rerank is async, but LangGraph handles it
    graph.add_edge("research", "rerank")
    graph.add_edge("rerank", "analysis")
    graph.add_edge("analysis", "synthesis")
    graph.add_edge("synthesis", END)
    
    return graph.compile()


# Create the compiled graph
SEQUENTIAL_AGENT = build_sequential_graph()


@traceable(name="run_sequential_agent", run_type="chain")
async def run_sequential_agent(
    question: str,
    session_id: str = "default",
    inference_mode: str = "balanced",
) -> dict:
    """
    Run the sequential multi-agent workflow.
    
    Args:
        question: User's question
        session_id: Session identifier
        
    Returns:
        Final state with answer and metadata
    """
    from multiagent.app.models.state import create_initial_state
    
    logger.info(f"🚀 Starting Sequential Multi-Agent workflow for: {question[:50]}...")
    
    # Create initial state
    initial_state = create_initial_state(
        question=question,
        session_id=session_id,
        pattern="sequential",
        inference_mode=inference_mode,  # type: ignore[arg-type]
    )
    
    try:
        # Run the graph (async because rerank node is async)
        final_state = await SEQUENTIAL_AGENT.ainvoke(initial_state)
        
        # Finalize state (calculate execution time)
        final_state = finalize_state(final_state)
        
        logger.info(f"✅ Sequential workflow complete in {final_state['execution_time']:.2f}s")
        
        return {
            "answer": final_state.get("final_answer", ""),
            "pattern": "sequential",
            "metadata": final_state.get("metadata", {}),
            "session_id": session_id,
            "execution_time": final_state.get("execution_time", 0.0)
        }
        
    except Exception as e:
        logger.error(f"❌ Sequential workflow error: {e}", exc_info=True)
        return {
            "answer": f"Error: {str(e)}",
            "pattern": "sequential",
            "error": str(e),
            "session_id": session_id,
            "execution_time": 0.0
        }

