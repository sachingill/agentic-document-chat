"""
Parallel Multi-Agent Workflow

Pattern: Multiple agents run in parallel → Evaluator selects best answer

This workflow runs multiple agents simultaneously and uses an Evaluator Agent
to select the best answer from all candidates.
"""

from langgraph.graph import StateGraph, END
from langsmith import traceable
import logging
import sys
import asyncio
from pathlib import Path
from typing import Dict, Any

# Import agents
from .research_agent import research_agent_node
from .evaluator_agent import evaluator_agent_node

# Import state
sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from multiagent.app.models.state import MultiAgentState, finalize_state

# Import existing RAG agents
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from app.agents.doc_agent import run_document_agent
from agentic.app.agents.agentic_agent import run_agentic_agent

logger = logging.getLogger(__name__)


@traceable(name="structured_rag_wrapper", run_type="chain")
async def structured_rag_wrapper_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Wrapper node to run Structured RAG agent.
    """
    question = state.get("question", "")
    session_id = state.get("session_id", "default")
    
    logger.info("🤖 Structured RAG Agent: Running...")
    
    try:
        answer = await run_document_agent(session_id, question)
        # Update candidate_answers
        candidate_answers = state.get("candidate_answers", {})
        candidate_answers["structured_rag"] = answer
        state["candidate_answers"] = candidate_answers
        logger.info("✅ Structured RAG Agent: Complete")
    except Exception as e:
        logger.error(f"❌ Structured RAG Agent error: {e}", exc_info=True)
        candidate_answers = state.get("candidate_answers", {})
        candidate_answers["structured_rag"] = f"Error: {str(e)}"
        state["candidate_answers"] = candidate_answers
    
    return state


@traceable(name="agentic_rag_wrapper", run_type="chain")
async def agentic_rag_wrapper_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Wrapper node to run Agentic RAG agent.
    """
    question = state.get("question", "")
    session_id = state.get("session_id", "default")
    
    logger.info("🤖 Agentic RAG Agent: Running...")
    
    try:
        answer = await run_agentic_agent(session_id, question)
        # Update candidate_answers
        candidate_answers = state.get("candidate_answers", {})
        candidate_answers["agentic_rag"] = answer
        state["candidate_answers"] = candidate_answers
        logger.info("✅ Agentic RAG Agent: Complete")
    except Exception as e:
        logger.error(f"❌ Agentic RAG Agent error: {e}", exc_info=True)
        candidate_answers = state.get("candidate_answers", {})
        candidate_answers["agentic_rag"] = f"Error: {str(e)}"
        state["candidate_answers"] = candidate_answers
    
    return state


@traceable(name="research_wrapper", run_type="chain")
def research_wrapper_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Wrapper node to run Research Agent and generate answer.
    """
    question = state.get("question", "")
    session_id = state.get("session_id", "default")
    
    logger.info("🤖 Research Agent: Running...")
    
    try:
        # Run research agent
        research_state = research_agent_node(state.copy())
        research_context = research_state.get("research_context", [])
        
        # Generate answer from research context
        if research_context:
            from multiagent.app.models.llm_providers import create_synthesis_llm
            synthesis_llm = create_synthesis_llm(temperature=0.1)
            
            context_text = "\n\n".join(research_context[:5])  # Limit to top 5
            
            prompt = f"""
You are a RAG assistant. Use ONLY the provided context to answer.

Context:
{context_text}

Question:
{question}

RULES:
- If answer is not found in context, respond: "I don't know based on the documents."
- Be concise and accurate
"""
            answer = synthesis_llm.invoke(prompt).content.strip()
        else:
            answer = "I don't know based on the documents."
        
        # Update candidate_answers
        candidate_answers = state.get("candidate_answers", {})
        candidate_answers["research_agent"] = answer
        state["candidate_answers"] = candidate_answers
        logger.info("✅ Research Agent: Complete")
    except Exception as e:
        logger.error(f"❌ Research Agent error: {e}", exc_info=True)
        candidate_answers = state.get("candidate_answers", {})
        candidate_answers["research_agent"] = f"Error: {str(e)}"
        state["candidate_answers"] = candidate_answers
    
    return state


@traceable(name="parallel_branch", run_type="chain")
async def parallel_branch_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute all agents in parallel.
    """
    logger.info("🚀 Parallel Branch: Starting parallel execution...")
    
    # Initialize candidate_answers
    state["candidate_answers"] = {}
    
    # Run all agents in parallel
    try:
        # Create tasks for async agents
        tasks = [
            structured_rag_wrapper_node(state.copy()),
            agentic_rag_wrapper_node(state.copy()),
        ]
        
        # Run async tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Update state with results
        for result in results:
            if isinstance(result, dict):
                candidate_answers = result.get("candidate_answers", {})
                state["candidate_answers"].update(candidate_answers)
        
        # Run synchronous research agent
        research_result = research_wrapper_node(state.copy())
        research_candidates = research_result.get("candidate_answers", {})
        state["candidate_answers"].update(research_candidates)
        
        logger.info(f"✅ Parallel Branch: Completed {len(state['candidate_answers'])} agents")
        
    except Exception as e:
        logger.error(f"❌ Parallel Branch error: {e}", exc_info=True)
        state["error"] = f"Parallel execution error: {str(e)}"
    
    return state


def build_parallel_graph():
    """
    Build the parallel multi-agent graph.
    
    Flow:
    1. Parallel Branch → Run all agents simultaneously
    2. Evaluator Agent → Select best answer
    3. END
    """
    graph = StateGraph(MultiAgentState)
    
    # Add nodes
    graph.add_node("parallel_branch", parallel_branch_node)
    graph.add_node("evaluator", evaluator_agent_node)
    
    # Set entry point
    graph.set_entry_point("parallel_branch")
    
    # Define flow: parallel_branch → evaluator → END
    graph.add_edge("parallel_branch", "evaluator")
    graph.add_edge("evaluator", END)
    
    return graph.compile()


# Create the compiled graph
PARALLEL_AGENT = build_parallel_graph()


@traceable(name="run_parallel_agent", run_type="chain")
async def run_parallel_agent(
    question: str,
    session_id: str = "default"
) -> dict:
    """
    Run the parallel multi-agent workflow.
    
    Args:
        question: User's question
        session_id: Session identifier
        
    Returns:
        Final state with answer and metadata
    """
    from multiagent.app.models.state import create_initial_state
    
    logger.info(f"🚀 Starting Parallel Multi-Agent workflow for: {question[:50]}...")
    
    # Create initial state
    initial_state = create_initial_state(
        question=question,
        session_id=session_id,
        pattern="parallel"
    )
    
    try:
        # Run the graph (async)
        final_state = await PARALLEL_AGENT.ainvoke(initial_state)
        
        # Finalize state (calculate execution time)
        final_state = finalize_state(final_state)
        
        logger.info(f"✅ Parallel workflow complete in {final_state['execution_time']:.2f}s")
        
        return {
            "answer": final_state.get("final_answer", final_state.get("selected_answer", "")),
            "pattern": "parallel",
            "selected_agent": final_state.get("selected_agent"),
            "evaluation_scores": final_state.get("evaluation_scores", {}),
            "evaluation_reasoning": final_state.get("evaluation_reasoning"),
            "metadata": final_state.get("metadata", {}),
            "session_id": session_id,
            "execution_time": final_state.get("execution_time", 0.0)
        }
        
    except Exception as e:
        logger.error(f"❌ Parallel workflow error: {e}", exc_info=True)
        return {
            "answer": f"Error: {str(e)}",
            "pattern": "parallel",
            "error": str(e),
            "session_id": session_id,
            "execution_time": 0.0
        }


