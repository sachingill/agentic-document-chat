"""
Comprehensive Evaluation Framework for RAG Systems
Evaluates both Structured RAG and Agentic RAG implementations

Focus Metrics:
1. Helpfulness - How helpful is the answer to the user?
2. Factual Consistency - Are the facts in the answer consistent with the context?

This evaluation framework provides:
- LLM-based evaluators for nuanced assessment
- Side-by-side comparison of Structured vs Agentic RAG
- Detailed reporting with actionable insights
"""

import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import logging

from langchain_openai import ChatOpenAI
from langsmith import traceable

# Import both RAG implementations
from app.agents.doc_agent import run_document_agent as run_structured_rag
from agentic.app.agents.agentic_agent import run_agentic_agent as run_agentic_rag

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# STEP 1: EVALUATION DATASET
# ============================================================================
# Action: Define test cases with questions and ground truth
# Reason: Need standardized test cases to compare both implementations fairly
# Impact: Ensures consistent evaluation across both systems
# ============================================================================

EVAL_DATASET = [
    {
        "question": "How does circuit breaker protect A1?",
        "ground_truth": "Circuit breaker protects A1 by opening when A1 returns 521 error storms and returning 429 Too Many Requests to prevent further load on the failing service.",
        "context": "system_design"
    },
    {
        "question": "What is SIM provisioning?",
        "ground_truth": "SIM provisioning is the process of activating and configuring a SIM card for use on a mobile network. The provisioning system triggers retry mechanisms when initial activation fails, using exponential backoff to prevent system overload.",
        "context": "telecom"
    },
    {
        "question": "How does the billing system process subscription updates?",
        "ground_truth": "Billing systems use BSS (Business Support Systems) pipeline to process subscription updates. The pipeline handles plan changes, payment processing, and account modifications in a transactional manner.",
        "context": "billing"
    },
    {
        "question": "What is API rate limiting?",
        "ground_truth": "API rate limiting prevents abuse and ensures fair resource allocation. Rate limits are enforced using token bucket algorithm, allowing burst traffic while maintaining average rate constraints.",
        "context": "api_design"
    },
    {
        "question": "How does connection pooling improve performance?",
        "ground_truth": "Database connection pooling improves application performance by reusing database connections. Connection pools maintain a set of pre-established connections, reducing connection overhead and latency.",
        "context": "database"
    },
    {
        "question": "What is microservices architecture?",
        "ground_truth": "Microservices architecture decomposes applications into small, independent services. Each service has its own database and communicates via APIs, enabling independent deployment and scaling.",
        "context": "architecture"
    },
    {
        "question": "How does load balancing work?",
        "ground_truth": "Load balancing distributes incoming network traffic across multiple servers to ensure high availability and reliability. Common algorithms include round-robin, least connections, and weighted distribution.",
        "context": "system_design"
    },
    {
        "question": "What are caching strategies?",
        "ground_truth": "Caching strategies improve application performance by storing frequently accessed data in fast storage. Redis and Memcached are popular in-memory caching solutions that reduce database load.",
        "context": "performance"
    }
]

# ============================================================================
# STEP 2: LLM-BASED EVALUATORS
# ============================================================================
# Action: Create LLM-based evaluators for helpfulness and factual consistency
# Reason: LLMs can understand nuance better than simple keyword matching
# Impact: More accurate and meaningful evaluation scores
# ============================================================================

evaluator_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


@traceable(name="evaluate_helpfulness", run_type="chain")
async def evaluate_helpfulness(
    question: str,
    answer: str,
    ground_truth: Optional[str] = None
) -> Dict[str, Any]:
    """
    Evaluate how helpful an answer is to the user.
    
    Action: Use LLM to assess answer quality from user perspective
    Reason: Helpfulness is subjective and requires understanding context
    Impact: Identifies answers that are technically correct but not useful
    
    Returns:
        {
            "score": float (0-1),
            "reasoning": str,
            "aspects": {
                "completeness": float,
                "clarity": float,
                "actionability": float
            }
        }
    """
    prompt = f"""
You are evaluating how helpful an answer is to a user's question.

Question: {question}

Answer to evaluate:
{answer}

{f"Expected answer (for reference): {ground_truth}" if ground_truth else ""}

Evaluate the answer on these dimensions:
1. **Completeness**: Does it fully address the question? (0-1)
2. **Clarity**: Is it clear and easy to understand? (0-1)
3. **Actionability**: Can the user act on this information? (0-1)

Consider:
- Does it answer what was asked?
- Is it too vague or too detailed?
- Would a user find this useful?
- Are there missing critical details?

Respond with JSON:
{{
    "overall_score": 0.0-1.0,
    "reasoning": "explanation of the score",
    "aspects": {{
        "completeness": 0.0-1.0,
        "clarity": 0.0-1.0,
        "actionability": 0.0-1.0
    }},
    "strengths": ["list of strengths"],
    "weaknesses": ["list of weaknesses"]
}}
"""
    
    try:
        response = evaluator_llm.invoke(prompt).content.strip()
        
        # Parse JSON response
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            response = response.split("```")[1].split("```")[0].strip()
        
        result = json.loads(response)
        
        return {
            "score": float(result.get("overall_score", 0.0)),
            "reasoning": result.get("reasoning", ""),
            "aspects": result.get("aspects", {}),
            "strengths": result.get("strengths", []),
            "weaknesses": result.get("weaknesses", [])
        }
    except Exception as e:
        logger.error(f"Error evaluating helpfulness: {e}")
        return {
            "score": 0.0,
            "reasoning": f"Evaluation error: {str(e)}",
            "aspects": {"completeness": 0.0, "clarity": 0.0, "actionability": 0.0},
            "strengths": [],
            "weaknesses": []
        }


@traceable(name="evaluate_factual_consistency", run_type="chain")
async def evaluate_factual_consistency(
    question: str,
    answer: str,
    context: List[str],
    ground_truth: Optional[str] = None
) -> Dict[str, Any]:
    """
    Evaluate if the answer is factually consistent with the provided context.
    
    Action: Check if facts in answer match facts in context
    Reason: Prevents hallucinations and ensures answers are grounded
    Impact: Identifies when system makes up information not in documents
    
    Returns:
        {
            "score": float (0-1),
            "reasoning": str,
            "claims": [
                {"claim": str, "supported": bool, "evidence": str}
            ]
        }
    """
    context_text = "\n\n".join(context) if context else "No context provided"
    
    prompt = f"""
You are evaluating if an answer is factually consistent with the provided context.

Question: {question}

Context (source documents):
{context_text}

Answer to evaluate:
{answer}

{f"Expected answer (for reference): {ground_truth}" if ground_truth else ""}

Your task:
1. Extract all factual claims from the answer
2. For each claim, check if it's supported by the context
3. Identify any claims that contradict the context
4. Identify any claims that are not in the context (hallucinations)

Consider:
- Are all facts in the answer present in the context?
- Are there any contradictions?
- Are there any unsupported claims?
- Is the answer grounded in the provided context?

Respond with JSON:
{{
    "overall_score": 0.0-1.0,
    "reasoning": "explanation of consistency score",
    "claims": [
        {{
            "claim": "specific factual claim from answer",
            "supported": true/false,
            "evidence": "quote from context that supports or contradicts"
        }}
    ],
    "hallucinations": ["list of unsupported claims"],
    "contradictions": ["list of contradictory claims"]
}}
"""
    
    try:
        response = evaluator_llm.invoke(prompt).content.strip()
        
        # Parse JSON response
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            response = response.split("```")[1].split("```")[0].strip()
        
        result = json.loads(response)
        
        return {
            "score": float(result.get("overall_score", 0.0)),
            "reasoning": result.get("reasoning", ""),
            "claims": result.get("claims", []),
            "hallucinations": result.get("hallucinations", []),
            "contradictions": result.get("contradictions", [])
        }
    except Exception as e:
        logger.error(f"Error evaluating factual consistency: {e}")
        return {
            "score": 0.0,
            "reasoning": f"Evaluation error: {str(e)}",
            "claims": [],
            "hallucinations": [],
            "contradictions": []
        }


# ============================================================================
# STEP 3: CONTEXT RETRIEVAL FOR EVALUATION
# ============================================================================
# Action: Retrieve contexts used by each system for comparison
# Reason: Need to evaluate factual consistency against actual retrieved context
# Impact: Ensures we evaluate what the system actually used, not ideal context
# ============================================================================

async def get_retrieved_context(question: str, system_type: str = "structured") -> List[str]:
    """
    Get the context that was actually retrieved by the system.
    
    Action: Simulate retrieval to get actual context used
    Reason: Need real context for factual consistency evaluation
    Impact: More accurate evaluation based on what system actually saw
    """
    from app.agents.tools import retrieve_tool
    
    try:
        result = retrieve_tool(question, k=5)
        return result.get("results", [])
    except Exception as e:
        logger.error(f"Error retrieving context: {e}")
        return []


# ============================================================================
# STEP 4: EVALUATION RUNNER
# ============================================================================
# Action: Run both systems and evaluate their outputs
# Reason: Need to compare structured vs agentic on same questions
# Impact: Provides actionable comparison data
# ============================================================================

@traceable(name="evaluate_single_question", run_type="chain")
async def evaluate_single_question(
    test_case: Dict[str, Any],
    system_type: str = "structured"
) -> Dict[str, Any]:
    """
    Evaluate a single question on one system.
    
    Action: Run system, get answer, evaluate helpfulness and factual consistency
    Reason: Need granular evaluation per question per system
    Impact: Enables detailed analysis and comparison
    """
    question = test_case["question"]
    ground_truth = test_case.get("ground_truth")
    session_id = f"eval-{system_type}-{hash(question) % 10000}"
    
    logger.info(f"  [{system_type.upper()}] Processing: {question[:60]}...")
    
    try:
        # Step 1: Run the system
        start_time = asyncio.get_event_loop().time()
        
        if system_type == "structured":
            answer = await run_structured_rag(session_id, question)
        elif system_type == "agentic":
            answer = await run_agentic_rag(session_id, question)
        else:
            raise ValueError(f"Unknown system type: {system_type}")
        
        elapsed_time = asyncio.get_event_loop().time() - start_time
        
        # Step 2: Get retrieved context
        context = await get_retrieved_context(question, system_type)
        
        # Step 3: Evaluate helpfulness
        helpfulness_result = await evaluate_helpfulness(question, answer, ground_truth)
        
        # Step 4: Evaluate factual consistency
        consistency_result = await evaluate_factual_consistency(
            question, answer, context, ground_truth
        )
        
        return {
            "question": question,
            "system_type": system_type,
            "answer": answer,
            "context_count": len(context),
            "elapsed_time": elapsed_time,
            "helpfulness": helpfulness_result,
            "factual_consistency": consistency_result,
            "ground_truth": ground_truth,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"  ❌ Error evaluating {system_type}: {e}")
        return {
            "question": question,
            "system_type": system_type,
            "answer": f"ERROR: {str(e)}",
            "context_count": 0,
            "elapsed_time": 0.0,
            "helpfulness": {"score": 0.0, "reasoning": f"Error: {str(e)}"},
            "factual_consistency": {"score": 0.0, "reasoning": f"Error: {str(e)}"},
            "ground_truth": ground_truth,
            "success": False
        }


# ============================================================================
# STEP 5: COMPREHENSIVE EVALUATION
# ============================================================================
# Action: Run evaluation on both systems for all test cases
# Reason: Need comprehensive comparison to make informed decisions
# Impact: Provides complete picture of system performance
# ============================================================================

async def run_comprehensive_evaluation() -> Dict[str, Any]:
    """
    Run comprehensive evaluation on both Structured and Agentic RAG.
    
    Action: Evaluate all test cases on both systems
    Reason: Need side-by-side comparison for decision making
    Impact: Identifies strengths/weaknesses of each approach
    """
    print("=" * 80)
    print("🚀 COMPREHENSIVE RAG EVALUATION")
    print("=" * 80)
    print(f"📊 Evaluating {len(EVAL_DATASET)} test cases on both systems\n")
    
    results = {
        "structured": [],
        "agentic": [],
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "test_cases_count": len(EVAL_DATASET),
            "evaluation_metrics": ["helpfulness", "factual_consistency"]
        }
    }
    
    # Evaluate each test case on both systems
    for i, test_case in enumerate(EVAL_DATASET, 1):
        print(f"\n[{i}/{len(EVAL_DATASET)}] {test_case['question'][:60]}...")
        print("-" * 80)
        
        # Evaluate on Structured RAG
        structured_result = await evaluate_single_question(test_case, "structured")
        results["structured"].append(structured_result)
        
        print(f"  ✅ Structured: Helpfulness={structured_result['helpfulness']['score']:.2f}, "
              f"Consistency={structured_result['factual_consistency']['score']:.2f}, "
              f"Time={structured_result['elapsed_time']:.2f}s")
        
        # Evaluate on Agentic RAG
        agentic_result = await evaluate_single_question(test_case, "agentic")
        results["agentic"].append(agentic_result)
        
        print(f"  ✅ Agentic: Helpfulness={agentic_result['helpfulness']['score']:.2f}, "
              f"Consistency={agentic_result['factual_consistency']['score']:.2f}, "
              f"Time={agentic_result['elapsed_time']:.2f}s")
    
    return results


# ============================================================================
# STEP 6: ANALYSIS AND REPORTING
# ============================================================================
# Action: Analyze results and generate comprehensive report
# Reason: Raw scores need interpretation to be actionable
# Impact: Provides clear insights for improvement
# ============================================================================

def analyze_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze evaluation results and compute aggregate metrics.
    
    Action: Calculate averages, identify patterns, find outliers
    Reason: Aggregate metrics reveal overall system performance
    Impact: Highlights areas needing improvement
    """
    structured = results["structured"]
    agentic = results["agentic"]
    
    def compute_metrics(system_results: List[Dict]) -> Dict[str, float]:
        helpfulness_scores = [r["helpfulness"]["score"] for r in system_results if r["success"]]
        consistency_scores = [r["factual_consistency"]["score"] for r in system_results if r["success"]]
        times = [r["elapsed_time"] for r in system_results if r["success"]]
        
        return {
            "avg_helpfulness": sum(helpfulness_scores) / len(helpfulness_scores) if helpfulness_scores else 0.0,
            "avg_consistency": sum(consistency_scores) / len(consistency_scores) if consistency_scores else 0.0,
            "avg_time": sum(times) / len(times) if times else 0.0,
            "success_rate": sum(1 for r in system_results if r["success"]) / len(system_results) if system_results else 0.0
        }
    
    structured_metrics = compute_metrics(structured)
    agentic_metrics = compute_metrics(agentic)
    
    return {
        "structured": structured_metrics,
        "agentic": agentic_metrics,
        "comparison": {
            "helpfulness_winner": "agentic" if agentic_metrics["avg_helpfulness"] > structured_metrics["avg_helpfulness"] else "structured",
            "consistency_winner": "agentic" if agentic_metrics["avg_consistency"] > structured_metrics["avg_consistency"] else "structured",
            "speed_winner": "structured" if structured_metrics["avg_time"] < agentic_metrics["avg_time"] else "agentic",
            "helpfulness_diff": agentic_metrics["avg_helpfulness"] - structured_metrics["avg_helpfulness"],
            "consistency_diff": agentic_metrics["avg_consistency"] - structured_metrics["avg_consistency"],
            "time_diff": agentic_metrics["avg_time"] - structured_metrics["avg_time"]
        }
    }


def generate_report(results: Dict[str, Any], analysis: Dict[str, Any]) -> str:
    """
    Generate human-readable evaluation report.
    
    Action: Format results into readable report
    Reason: Makes evaluation results accessible to stakeholders
    Impact: Enables data-driven decision making
    """
    report = []
    report.append("=" * 80)
    report.append("📊 COMPREHENSIVE RAG EVALUATION REPORT")
    report.append("=" * 80)
    report.append(f"Generated: {results['metadata']['timestamp']}")
    report.append(f"Test Cases: {results['metadata']['test_cases_count']}")
    report.append("")
    
    # Summary
    report.append("📈 SUMMARY METRICS")
    report.append("-" * 80)
    report.append(f"{'Metric':<25} {'Structured':<15} {'Agentic':<15} {'Winner':<15}")
    report.append("-" * 80)
    
    structured = analysis["structured"]
    agentic = analysis["agentic"]
    comp = analysis["comparison"]
    
    report.append(f"{'Helpfulness (avg)':<25} {structured['avg_helpfulness']:<15.2%} {agentic['avg_helpfulness']:<15.2%} {comp['helpfulness_winner']:<15}")
    report.append(f"{'Consistency (avg)':<25} {structured['avg_consistency']:<15.2%} {agentic['avg_consistency']:<15.2%} {comp['consistency_winner']:<15}")
    report.append(f"{'Avg Time (seconds)':<25} {structured['avg_time']:<15.2f} {agentic['avg_time']:<15.2f} {comp['speed_winner']:<15}")
    report.append(f"{'Success Rate':<25} {structured['success_rate']:<15.2%} {agentic['success_rate']:<15.2%}")
    report.append("")
    
    # Detailed comparison
    report.append("🔍 DETAILED COMPARISON")
    report.append("-" * 80)
    report.append(f"Helpfulness Difference: {comp['helpfulness_diff']:+.2%} (Agentic vs Structured)")
    report.append(f"Consistency Difference: {comp['consistency_diff']:+.2%} (Agentic vs Structured)")
    report.append(f"Time Difference: {comp['time_diff']:+.2f}s (Agentic vs Structured)")
    report.append("")
    
    # Per-question breakdown
    report.append("📋 PER-QUESTION BREAKDOWN")
    report.append("-" * 80)
    
    for i, (s_result, a_result) in enumerate(zip(results["structured"], results["agentic"]), 1):
        report.append(f"\n[{i}] {s_result['question'][:70]}")
        report.append(f"  Structured: H={s_result['helpfulness']['score']:.2f}, C={s_result['factual_consistency']['score']:.2f}, T={s_result['elapsed_time']:.2f}s")
        report.append(f"  Agentic:    H={a_result['helpfulness']['score']:.2f}, C={a_result['factual_consistency']['score']:.2f}, T={a_result['elapsed_time']:.2f}s")
    
    return "\n".join(report)


# ============================================================================
# STEP 7: MAIN EXECUTION
# ============================================================================
# Action: Run complete evaluation pipeline
# Reason: Orchestrates all steps in correct order
# Impact: Provides end-to-end evaluation workflow
# ============================================================================

async def main():
    """Main evaluation pipeline."""
    # Step 1: Run evaluation
    results = await run_comprehensive_evaluation()
    
    # Step 2: Analyze results
    print("\n" + "=" * 80)
    print("📊 Analyzing Results...")
    print("=" * 80)
    analysis = analyze_results(results)
    
    # Step 3: Generate report
    report = generate_report(results, analysis)
    print("\n" + report)
    
    # Step 4: Save results
    output_dir = Path("evaluation_results")
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save detailed results (JSON)
    results_file = output_dir / f"eval_results_{timestamp}.json"
    with open(results_file, "w") as f:
        json.dump({**results, "analysis": analysis}, f, indent=2)
    print(f"\n💾 Detailed results saved to: {results_file}")
    
    # Save report (text)
    report_file = output_dir / f"eval_report_{timestamp}.txt"
    with open(report_file, "w") as f:
        f.write(report)
    print(f"💾 Report saved to: {report_file}")
    
    return results, analysis


if __name__ == "__main__":
    asyncio.run(main())

