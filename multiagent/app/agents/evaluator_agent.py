"""
Evaluator Agent

Specialized in evaluating and comparing multiple answers.
Scores answers on multiple criteria and selects the best one.
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

# LLM for evaluation (needs reasoning capability, supports multiple providers)
evaluator_llm = create_reasoning_llm(temperature=0.1)


@traceable(name="evaluator_agent", run_type="chain")
def evaluator_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluator Agent: Evaluates and compares multiple answers.
    
    Process:
    1. Read candidate_answers from parallel agents
    2. Evaluate each answer on multiple criteria:
       - Relevance to question
       - Completeness
       - Clarity
       - Usefulness
    3. Score each answer (0.0-1.0)
    4. Select best answer
    5. Provide reasoning
    
    Args:
        state: MultiAgentState with candidate_answers
        
    Returns:
        Updated state with selected_answer, evaluation_scores, evaluation_reasoning
    """
    question = state.get("question", "")
    candidate_answers = state.get("candidate_answers", {})
    
    logger.info(f"🔍 Evaluator Agent: Evaluating {len(candidate_answers)} candidate answers")
    
    if not candidate_answers:
        logger.warning("No candidate answers to evaluate")
        state["selected_answer"] = "No answers were generated."
        state["evaluation_scores"] = {}
        state["evaluation_reasoning"] = "No candidate answers available."
        state["selected_agent"] = None
        return state
    
    try:
        # Format candidate answers for evaluation
        formatted_answers = []
        for agent_name, answer in candidate_answers.items():
            formatted_answers.append(f"Agent: {agent_name}\nAnswer: {answer}\n")
        
        formatted_answers_text = "\n---\n".join(formatted_answers)
        
        # Build evaluation prompt
        evaluation_prompt = f"""
You are an evaluator agent. Evaluate the following answers and select the best one.

Question: {question}

Candidate Answers:
{formatted_answers_text}

Evaluate each answer on the following criteria (0.0-1.0):
1. Relevance: How well does it answer the question?
2. Completeness: Does it cover all aspects of the question?
3. Clarity: Is it easy to understand?
4. Usefulness: Is it actionable/helpful?

Respond with JSON:
{{
    "evaluations": [
        {{
            "agent_name": "agent_name",
            "relevance": 0.0-1.0,
            "completeness": 0.0-1.0,
            "clarity": 0.0-1.0,
            "usefulness": 0.0-1.0,
            "overall_score": 0.0-1.0,
            "reasoning": "brief explanation"
        }}
    ],
    "selected_agent": "agent_name",
    "selection_reasoning": "why this answer was selected"
}}
"""
        
        response = evaluator_llm.invoke(evaluation_prompt).strip()
        
        # Parse JSON response
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            response = response.split("```")[1].split("```")[0].strip()
        
        try:
            evaluation_result = json.loads(response)
            evaluations = evaluation_result.get("evaluations", [])
            selected_agent = evaluation_result.get("selected_agent", "")
            selection_reasoning = evaluation_result.get("selection_reasoning", "")
            
            # Build evaluation scores dict
            evaluation_scores = {}
            for eval_data in evaluations:
                agent_name = eval_data.get("agent_name", "")
                overall_score = eval_data.get("overall_score", 0.0)
                evaluation_scores[agent_name] = overall_score
            
            # Get selected answer
            selected_answer = candidate_answers.get(selected_agent, "")
            
            if not selected_answer:
                # Fallback: select answer with highest score
                if evaluation_scores:
                    selected_agent = max(evaluation_scores.items(), key=lambda x: x[1])[0]
                    selected_answer = candidate_answers.get(selected_agent, "")
            
            # Update state
            state["selected_answer"] = selected_answer
            state["selected_agent"] = selected_agent
            state["evaluation_scores"] = evaluation_scores
            state["evaluation_reasoning"] = selection_reasoning
            state["final_answer"] = selected_answer  # Also set final_answer
            
            logger.info(f"✅ Evaluator Agent: Selected '{selected_agent}' with score {evaluation_scores.get(selected_agent, 0.0):.2f}")
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse evaluation JSON: {e}, using fallback")
            # Fallback: select first answer
            first_agent = list(candidate_answers.keys())[0]
            state["selected_answer"] = candidate_answers[first_agent]
            state["selected_agent"] = first_agent
            state["evaluation_scores"] = {first_agent: 0.5}
            state["evaluation_reasoning"] = "Fallback selection due to parsing error"
            state["final_answer"] = candidate_answers[first_agent]
        
    except Exception as e:
        logger.error(f"❌ Evaluator Agent error: {e}", exc_info=True)
        state["error"] = f"Evaluator Agent error: {str(e)}"
        # Fallback: select first answer
        if candidate_answers:
            first_agent = list(candidate_answers.keys())[0]
            state["selected_answer"] = candidate_answers[first_agent]
            state["selected_agent"] = first_agent
            state["evaluation_scores"] = {first_agent: 0.5}
            state["evaluation_reasoning"] = "Fallback selection due to error"
            state["final_answer"] = candidate_answers[first_agent]
        else:
            state["selected_answer"] = "Error during evaluation."
            state["selected_agent"] = None
            state["evaluation_scores"] = {}
            state["evaluation_reasoning"] = "Error during evaluation"
    
    return state


