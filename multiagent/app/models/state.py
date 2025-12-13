"""
Multi-Agent State Definition

This module defines the state structure for multi-agent workflows.
"""

from typing import TypedDict, List, Dict, Optional, Literal, Any
import time


class MultiAgentState(TypedDict):
    """
    State structure for multi-agent workflows.
    
    Supports three patterns:
    1. Sequential: Research → Analysis → Synthesis
    2. Parallel: Multiple agents compete → Evaluator selects best
    3. Supervisor-Worker: Supervisor delegates → Workers execute → Supervisor combines
    """
    # Core fields (always present)
    session_id: str
    question: str
    final_answer: str
    pattern: Literal["sequential", "parallel", "supervisor"]
    
    # Sequential pattern fields
    research_context: Optional[List[str]]  # Research Agent output
    analyzed_info: Optional[str]  # Analysis Agent output
    key_points: Optional[List[str]]  # Extracted key points
    relationships: Optional[List[str]]  # Identified relationships
    
    # Parallel pattern fields
    candidate_answers: Optional[Dict[str, str]]  # {agent_name: answer}
    evaluation_scores: Optional[Dict[str, float]]  # {agent_name: score}
    selected_answer: Optional[str]  # Evaluator's choice
    selected_agent: Optional[str]  # Which agent produced best answer
    evaluation_reasoning: Optional[str]  # Why this answer was selected
    
    # Supervisor pattern fields
    supervisor_plan: Optional[str]  # Supervisor's task plan
    workers_used: Optional[List[str]]  # Which workers were used
    worker_results: Optional[Dict[str, Any]]  # {worker_name: result}
    combined_result: Optional[str]  # Supervisor's combined result
    
    # Common fields
    context: List[str]  # Accumulated context
    metadata: Dict[str, Any]  # Additional metadata
    error: Optional[str]  # Error message if any
    iteration_count: int  # Track iterations
    execution_time: float  # Total execution time


def create_initial_state(
    question: str,
    session_id: str,
    pattern: Literal["sequential", "parallel", "supervisor"] = "sequential"
) -> MultiAgentState:
    """
    Create initial state for multi-agent workflow.
    
    Args:
        question: User's question
        session_id: Session identifier
        pattern: Which workflow pattern to use
        
    Returns:
        Initialized MultiAgentState
    """
    start_time = time.time()
    
    return {
        "session_id": session_id,
        "question": question,
        "final_answer": "",
        "pattern": pattern,
        "research_context": None,
        "analyzed_info": None,
        "key_points": None,
        "relationships": None,
        "candidate_answers": None,
        "evaluation_scores": None,
        "selected_answer": None,
        "selected_agent": None,
        "evaluation_reasoning": None,
        "supervisor_plan": None,
        "workers_used": None,
        "worker_results": None,
        "combined_result": None,
        "context": [],
        "metadata": {"start_time": start_time},
        "error": None,
        "iteration_count": 0,
        "execution_time": 0.0
    }


def finalize_state(state: MultiAgentState) -> MultiAgentState:
    """
    Finalize state by calculating execution time.
    
    Args:
        state: Current state
        
    Returns:
        State with execution_time calculated
    """
    if "start_time" in state.get("metadata", {}):
        start_time = state["metadata"]["start_time"]
        state["execution_time"] = time.time() - start_time
    
    return state

