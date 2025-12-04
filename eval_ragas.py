"""
RAGAS Evaluation - Local RAG Evaluation Framework
No cloud dependencies, runs 100% locally
"""

import asyncio
from typing import List, Dict
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall
)
from app.agents.doc_agent import run_document_agent
from app.agents.tools import retrieve_tool
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test dataset
TEST_DATASET = [
    {
        "question": "How does circuit breaker protect A1?",
        "ground_truth": "Circuit breaker protects A1 by opening when A1 returns 521 error storms and returning 429 Too Many Requests to prevent further load on the failing service."
    },
    {
        "question": "What is SIM provisioning?",
        "ground_truth": "SIM provisioning is the process of activating and configuring a SIM card for use on a mobile network. The provisioning system triggers retry mechanisms when initial activation fails, using exponential backoff to prevent system overload."
    },
    {
        "question": "How does the billing system process subscription updates?",
        "ground_truth": "Billing systems use BSS (Business Support Systems) pipeline to process subscription updates. The pipeline handles plan changes, payment processing, and account modifications in a transactional manner."
    },
    {
        "question": "What is API rate limiting?",
        "ground_truth": "API rate limiting prevents abuse and ensures fair resource allocation. Rate limits are enforced using token bucket algorithm, allowing burst traffic while maintaining average rate constraints."
    },
    {
        "question": "How does connection pooling improve performance?",
        "ground_truth": "Database connection pooling improves application performance by reusing database connections. Connection pools maintain a set of pre-established connections, reducing connection overhead and latency."
    },
    {
        "question": "What is microservices architecture?",
        "ground_truth": "Microservices architecture decomposes applications into small, independent services. Each service has its own database and communicates via APIs, enabling independent deployment and scaling."
    },
    {
        "question": "How does load balancing work?",
        "ground_truth": "Load balancing distributes incoming network traffic across multiple servers to ensure high availability and reliability. Common algorithms include round-robin, least connections, and weighted distribution."
    },
    {
        "question": "What are caching strategies?",
        "ground_truth": "Caching strategies improve application performance by storing frequently accessed data in fast storage. Redis and Memcached are popular in-memory caching solutions that reduce database load."
    }
]


async def get_contexts_for_question(question: str, k: int = 5) -> List[str]:
    """
    Retrieve contexts for a question (simulating what RAG system retrieves).
    This is needed for RAGAS evaluation.
    """
    try:
        result = retrieve_tool(question, k=k)
        contexts = result.get("results", [])
        return contexts if contexts else ["No context found"]
    except Exception as e:
        logger.error(f"Error retrieving contexts: {e}")
        return ["Error retrieving context"]


async def create_eval_dataset() -> Dataset:
    """
    Create evaluation dataset by running RAG system on test cases.
    """
    logger.info("Creating evaluation dataset...")
    
    questions = []
    answers = []
    contexts_list = []
    ground_truths = []
    
    for i, test_case in enumerate(TEST_DATASET, 1):
        question = test_case["question"]
        ground_truth = test_case["ground_truth"]
        
        logger.info(f"[{i}/{len(TEST_DATASET)}] Processing: {question[:50]}...")
        
        try:
            # Run RAG agent to get answer
            answer = await run_document_agent(
                session_id=f"ragas-eval-{i}",
                question=question
            )
            
            # Get contexts (what was retrieved)
            contexts = await get_contexts_for_question(question, k=5)
            
            questions.append(question)
            answers.append(answer)
            contexts_list.append(contexts)
            ground_truths.append(ground_truth)
            
            logger.info(f"  ✅ Answer length: {len(answer)} chars, Contexts: {len(contexts)}")
            
        except Exception as e:
            logger.error(f"  ❌ Error: {e}")
            # Add placeholder data
            questions.append(question)
            answers.append(f"ERROR: {str(e)}")
            contexts_list.append(["Error occurred"])
            ground_truths.append(ground_truth)
    
    # Create dataset
    dataset = Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts_list,
        "ground_truth": ground_truths
    })
    
    logger.info(f"✅ Dataset created with {len(questions)} examples")
    return dataset


async def run_ragas_evaluation():
    """
    Run RAGAS evaluation on the RAG system.
    """
    print("🚀 Starting RAGAS Evaluation (Local)")
    print("=" * 60)
    
    # Create dataset
    dataset = await create_eval_dataset()
    
    print("\n📊 Running RAGAS Metrics...")
    print("=" * 60)
    
    # Run evaluation with RAGAS metrics
    try:
        results = evaluate(
            dataset,
            metrics=[
                faithfulness,        # Answer is grounded in context
                answer_relevancy,    # Answer is relevant to question
                context_precision,   # Retrieved context is relevant
                context_recall       # All relevant context was retrieved
            ]
        )
        
        print("\n" + "=" * 60)
        print("📈 Evaluation Results")
        print("=" * 60)
        print(results)
        print("=" * 60)
        
        # Extract metrics
        metrics_df = results.to_pandas()
        
        print("\n📊 Summary Statistics:")
        print("-" * 60)
        print(f"Faithfulness:      {metrics_df['faithfulness'].mean():.2%} (avg)")
        print(f"Answer Relevancy:  {metrics_df['answer_relevancy'].mean():.2%} (avg)")
        print(f"Context Precision: {metrics_df['context_precision'].mean():.2%} (avg)")
        print(f"Context Recall:    {metrics_df['context_recall'].mean():.2%} (avg)")
        print("-" * 60)
        
        # Save results
        metrics_df.to_csv("ragas_eval_results.csv", index=False)
        print("\n💾 Results saved to: ragas_eval_results.csv")
        
        return results
        
    except Exception as e:
        logger.error(f"Error during evaluation: {e}")
        print(f"\n❌ Evaluation failed: {e}")
        print("\n💡 Make sure you have installed RAGAS:")
        print("   pip install ragas datasets")
        raise


if __name__ == "__main__":
    # Run evaluation
    asyncio.run(run_ragas_evaluation())

