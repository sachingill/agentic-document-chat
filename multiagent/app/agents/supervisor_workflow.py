"""
Supervisor-Worker Multi-Agent Workflow

Pattern: Supervisor delegates → Workers execute → Supervisor combines

This workflow uses a Supervisor Agent to analyze questions and delegate tasks
to specialized Worker Agents, then combines their results.
"""

from langgraph.graph import StateGraph, END
from langsmith import traceable
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Literal

# Import agents
from .supervisor_agent import supervisor_planning_node, supervisor_combine_node
from .workers import (
    retrieval_worker_node,
    analysis_worker_node,
    code_worker_node,
    comparison_worker_node,
    explanation_worker_node
)

# Import state
sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from multiagent.app.models.state import MultiAgentState, finalize_state

logger = logging.getLogger(__name__)

# Worker mapping
WORKER_MAP = {
    "RetrievalWorker": retrieval_worker_node,
    "AnalysisWorker": analysis_worker_node,
    "CodeWorker": code_worker_node,
    "ComparisonWorker": comparison_worker_node,
    "ExplanationWorker": explanation_worker_node
}


def route_to_workers(state: Dict[str, Any]) -> Literal["retrieval_worker", "analysis_worker", "code_worker", "comparison_worker", "explanation_worker", "combine"]:
    """
    Route to appropriate workers based on supervisor's plan.
    
    Executes workers in order, checking which ones haven't run yet.
    """
    workers_used = state.get("workers_used", [])
    worker_results = state.get("worker_results", {})
    
    # Execute workers in order
    worker_order = ["RetrievalWorker", "AnalysisWorker", "CodeWorker", "ComparisonWorker", "ExplanationWorker"]
    
    for worker_name in worker_order:
        if worker_name in workers_used and worker_name not in worker_results:
            # Map to node name
            node_map = {
                "RetrievalWorker": "retrieval_worker",
                "AnalysisWorker": "analysis_worker",
                "CodeWorker": "code_worker",
                "ComparisonWorker": "comparison_worker",
                "ExplanationWorker": "explanation_worker"
            }
            return node_map.get(worker_name, "combine")
    
    # All workers done, go to combine
    return "combine"


@traceable(name="worker_execution", run_type="chain")
def worker_execution_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check which workers need to run and route accordingly.
    
    This is a routing node that checks the state and routes to the next worker.
    """
    # This node just passes through - actual routing happens via conditional edges
    return state


def build_supervisor_graph():
    """
    Build the supervisor-worker multi-agent graph.
    
    Flow:
    1. Supervisor Planning → Analyze question, create plan
    2. Worker Execution → Execute selected workers
    3. Supervisor Combine → Combine results into final answer
    4. END
    """
    graph = StateGraph(MultiAgentState)
    
    # Add nodes
    graph.add_node("supervisor_planning", supervisor_planning_node)
    graph.add_node("worker_execution", worker_execution_node)
    graph.add_node("combine", supervisor_combine_node)
    
    # Add worker nodes (they'll be called from worker_execution_node)
    graph.add_node("retrieval_worker", retrieval_worker_node)
    graph.add_node("analysis_worker", analysis_worker_node)
    graph.add_node("code_worker", code_worker_node)
    graph.add_node("comparison_worker", comparison_worker_node)
    graph.add_node("explanation_worker", explanation_worker_node)
    
    # Set entry point
    graph.set_entry_point("supervisor_planning")
    
    # Define flow: supervisor_planning → worker_execution → [workers] → combine → END
    graph.add_edge("supervisor_planning", "worker_execution")
    
    # Conditional routing from worker_execution to workers
    graph.add_conditional_edges(
        "worker_execution",
        route_to_workers,
        {
            "retrieval_worker": "retrieval_worker",
            "analysis_worker": "analysis_worker",
            "code_worker": "code_worker",
            "comparison_worker": "comparison_worker",
            "explanation_worker": "explanation_worker",
            "combine": "combine"
        }
    )
    
    # All workers route back to worker_execution to check for more workers
    graph.add_edge("retrieval_worker", "worker_execution")
    graph.add_edge("analysis_worker", "worker_execution")
    graph.add_edge("code_worker", "worker_execution")
    graph.add_edge("comparison_worker", "worker_execution")
    graph.add_edge("explanation_worker", "worker_execution")
    
    # Combine routes to END
    graph.add_edge("combine", END)
    
    return graph.compile()


# Create the compiled graph
SUPERVISOR_AGENT = build_supervisor_graph()


@traceable(name="run_supervisor_agent", run_type="chain")
def run_supervisor_agent(
    question: str,
    session_id: str = "default",
    inference_mode: str = "balanced",
) -> dict:
    """
    Run the supervisor-worker multi-agent workflow.
    
    Args:
        question: User's question
        session_id: Session identifier
        
    Returns:
        Final state with answer and metadata
    """
    from multiagent.app.models.state import create_initial_state
    
    logger.info(f"🚀 Starting Supervisor-Worker Multi-Agent workflow for: {question[:50]}...")
    
    # Create initial state
    initial_state = create_initial_state(
        question=question,
        session_id=session_id,
        pattern="supervisor",
        inference_mode=inference_mode,  # type: ignore[arg-type]
    )
    
    try:
        # Run the graph
        final_state = SUPERVISOR_AGENT.invoke(initial_state)
        
        # Finalize state (calculate execution time)
        final_state = finalize_state(final_state)
        
        logger.info(f"✅ Supervisor-Worker workflow complete in {final_state['execution_time']:.2f}s")
        
        return {
            "answer": final_state.get("final_answer", ""),
            "pattern": "supervisor",
            "supervisor_plan": final_state.get("supervisor_plan"),
            "workers_used": final_state.get("workers_used", []),
            "metadata": final_state.get("metadata", {}),
            "session_id": session_id,
            "execution_time": final_state.get("execution_time", 0.0)
        }
        
    except Exception as e:
        logger.error(f"❌ Supervisor-Worker workflow error: {e}", exc_info=True)
        return {
            "answer": f"Error: {str(e)}",
            "pattern": "supervisor",
            "error": str(e),
            "session_id": session_id,
            "execution_time": 0.0
        }



