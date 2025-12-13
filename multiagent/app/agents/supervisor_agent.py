"""
Supervisor Agent

Coordinates and delegates tasks to worker agents.
Analyzes question complexity and determines which workers are needed.
"""

from typing import Dict, Any, List
from langsmith import traceable
import logging
import sys
import json
from pathlib import Path

# Import LLM factory for multi-provider support
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from multiagent.app.models.llm_providers import create_reasoning_llm

logger = logging.getLogger(__name__)

# LLM for supervisor (needs planning capability, supports multiple providers)
supervisor_llm = create_reasoning_llm(temperature=0.1)


@traceable(name="supervisor_planning", run_type="chain")
def supervisor_planning_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Supervisor Agent: Analyzes question and creates task plan.
    
    Process:
    1. Analyze question complexity
    2. Determine required workers
    3. Create task plan
    4. Delegate tasks to workers
    
    Args:
        state: MultiAgentState with question
        
    Returns:
        Updated state with supervisor_plan, workers_used
    """
    question = state.get("question", "")
    
    logger.info(f"👔 Supervisor Agent: Planning for: {question[:50]}...")
    
    try:
        # Build planning prompt
        planning_prompt = f"""
You are a supervisor agent. Analyze the question and create a task plan.

Question: {question}

Available workers:
- RetrievalWorker: Document retrieval and information gathering
- AnalysisWorker: Information analysis and structuring
- CodeWorker: Code-related queries and examples
- ComparisonWorker: Compare multiple topics or concepts
- ExplanationWorker: Conceptual explanations and definitions

Your task:
1. Analyze the question complexity
2. Determine which workers are needed
3. Create a task plan for each worker
4. Explain why each worker is needed

Respond with JSON:
{{
    "complexity": "simple" | "medium" | "complex",
    "workers_needed": ["worker1", "worker2", ...],
    "task_plan": {{
        "worker1": "specific task description",
        "worker2": "specific task description"
    }},
    "reasoning": "why these workers were selected"
}}
"""
        
        response = supervisor_llm.invoke(planning_prompt).strip()
        
        # Parse JSON response
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            response = response.split("```")[1].split("```")[0].strip()
        
        try:
            plan_result = json.loads(response)
            workers_needed = plan_result.get("workers_needed", [])
            task_plan = plan_result.get("task_plan", {})
            reasoning = plan_result.get("reasoning", "")
            
            # Update state
            state["supervisor_plan"] = json.dumps(plan_result, indent=2)
            state["workers_used"] = workers_needed
            state["worker_results"] = {}
            state["metadata"] = state.get("metadata", {})
            state["metadata"]["supervisor_reasoning"] = reasoning
            state["metadata"]["complexity"] = plan_result.get("complexity", "medium")
            
            logger.info(f"✅ Supervisor Agent: Selected {len(workers_needed)} workers: {workers_needed}")
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse planning JSON: {e}, using default workers")
            # Fallback: use default workers
            default_workers = ["RetrievalWorker", "AnalysisWorker"]
            state["supervisor_plan"] = "Default plan: Use RetrievalWorker and AnalysisWorker"
            state["workers_used"] = default_workers
            state["worker_results"] = {}
            state["metadata"] = state.get("metadata", {})
            state["metadata"]["supervisor_reasoning"] = "Fallback to default workers"
        
    except Exception as e:
        logger.error(f"❌ Supervisor Planning error: {e}", exc_info=True)
        state["error"] = f"Supervisor Planning error: {str(e)}"
        # Fallback
        state["supervisor_plan"] = "Error during planning"
        state["workers_used"] = ["RetrievalWorker"]
        state["worker_results"] = {}
    
    return state


@traceable(name="supervisor_combine", run_type="chain")
def supervisor_combine_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Supervisor Agent: Combines worker results into final answer.
    
    Process:
    1. Read all worker results
    2. Combine into comprehensive answer
    3. Generate final formatted answer
    
    Args:
        state: MultiAgentState with worker_results
        
    Returns:
        Updated state with combined_result, final_answer
    """
    question = state.get("question", "")
    worker_results = state.get("worker_results", {})
    
    logger.info(f"👔 Supervisor Agent: Combining {len(worker_results)} worker results")
    
    if not worker_results:
        logger.warning("No worker results to combine")
        state["combined_result"] = "No results from workers."
        state["final_answer"] = "I don't know based on the documents."
        return state
    
    try:
        # Format worker results
        formatted_results = []
        for worker_name, result in worker_results.items():
            if isinstance(result, dict):
                result_text = result.get("answer", result.get("result", str(result)))
            else:
                result_text = str(result)
            formatted_results.append(f"Worker: {worker_name}\nResult: {result_text}\n")
        
        formatted_results_text = "\n---\n".join(formatted_results)
        
        # Build combination prompt
        combine_prompt = f"""
You are a supervisor agent. Combine the following worker results into a comprehensive answer.

Question: {question}

Worker Results:
{formatted_results_text}

Your task:
1. Synthesize all worker results into a coherent answer
2. Ensure the answer directly addresses the question
3. Combine information from all workers appropriately
4. Make it comprehensive but well-structured
5. Remove any redundancy

Provide a well-structured, comprehensive answer.
"""
        
        from multiagent.app.models.llm_providers import create_synthesis_llm
        synthesis_llm = create_synthesis_llm(temperature=0.1)
        
        response = synthesis_llm.invoke(combine_prompt).strip()
        combined_answer = response
        
        # Update state
        state["combined_result"] = combined_answer
        state["final_answer"] = combined_answer
        
        logger.info(f"✅ Supervisor Agent: Combined results into answer ({len(combined_answer)} chars)")
        
    except Exception as e:
        logger.error(f"❌ Supervisor Combine error: {e}", exc_info=True)
        state["error"] = f"Supervisor Combine error: {str(e)}"
        # Fallback: use first worker result
        if worker_results:
            first_result = list(worker_results.values())[0]
            if isinstance(first_result, dict):
                fallback_answer = first_result.get("answer", first_result.get("result", str(first_result)))
            else:
                fallback_answer = str(first_result)
            state["combined_result"] = fallback_answer
            state["final_answer"] = fallback_answer
        else:
            state["combined_result"] = "Error combining results."
            state["final_answer"] = "I don't know based on the documents."
    
    return state


