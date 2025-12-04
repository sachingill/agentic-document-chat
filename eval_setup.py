"""
Evaluation Setup for RAG System
Uses LangSmith for evaluation tracking and metrics
"""

import os
from typing import List, Dict, Any
from langsmith import Client, evaluate
from langsmith.evaluation import evaluate, LangChainStringEvaluator
from langchain_openai import ChatOpenAI
from app.agents.doc_agent import run_document_agent
import asyncio
import json

# Initialize LangSmith client
client = Client(api_key=os.getenv("LANGSMITH_API_KEY"))

# Golden dataset for evaluation
EVAL_DATASET = [
    {
        "question": "How does circuit breaker protect A1?",
        "expected_answer": "Circuit breaker protects A1 by opening when A1 returns 521 error storms and returning 429 Too Many Requests to prevent further load on the failing service.",
        "context": "circuit_breaker"
    },
    {
        "question": "What is SIM provisioning?",
        "expected_answer": "SIM provisioning is the process of activating and configuring a SIM card for use on a mobile network. The provisioning system triggers retry mechanisms when initial activation fails.",
        "context": "provisioning"
    },
    {
        "question": "How does the billing system process subscription updates?",
        "expected_answer": "Billing systems use BSS (Business Support Systems) pipeline to process subscription updates. The pipeline handles plan changes, payment processing, and account modifications in a transactional manner.",
        "context": "billing"
    },
    {
        "question": "What is API rate limiting?",
        "expected_answer": "API rate limiting prevents abuse and ensures fair resource allocation. Rate limits are enforced using token bucket algorithm, allowing burst traffic while maintaining average rate constraints.",
        "context": "rate_limiting"
    },
    {
        "question": "How does connection pooling improve performance?",
        "expected_answer": "Database connection pooling improves application performance by reusing database connections. Connection pools maintain a set of pre-established connections, reducing connection overhead and latency.",
        "context": "database"
    },
    {
        "question": "What is microservices architecture?",
        "expected_answer": "Microservices architecture decomposes applications into small, independent services. Each service has its own database and communicates via APIs, enabling independent deployment and scaling.",
        "context": "architecture"
    },
    {
        "question": "How does load balancing work?",
        "expected_answer": "Load balancing distributes incoming network traffic across multiple servers to ensure high availability and reliability. Common algorithms include round-robin, least connections, and weighted distribution.",
        "context": "load_balancing"
    },
    {
        "question": "What are caching strategies?",
        "expected_answer": "Caching strategies improve application performance by storing frequently accessed data in fast storage. Redis and Memcached are popular in-memory caching solutions that reduce database load.",
        "context": "caching"
    },
    {
        "question": "What is message queue?",
        "expected_answer": "Message queues enable asynchronous communication between services. RabbitMQ and Apache Kafka are popular message brokers that support pub-sub patterns and reliable message delivery.",
        "context": "messaging"
    },
    {
        "question": "What is container orchestration?",
        "expected_answer": "Container orchestration platforms like Kubernetes manage containerized applications at scale. They handle deployment, scaling, load balancing, and self-healing of container clusters.",
        "context": "orchestration"
    }
]


async def run_evaluation():
    """
    Run evaluation on the RAG system using LangSmith.
    """
    print("🚀 Starting RAG System Evaluation...")
    print(f"📊 Evaluating {len(EVAL_DATASET)} test cases\n")
    
    results = []
    
    for i, test_case in enumerate(EVAL_DATASET, 1):
        question = test_case["question"]
        expected = test_case["expected_answer"]
        context = test_case.get("context", "")
        
        print(f"[{i}/{len(EVAL_DATASET)}] Testing: {question[:50]}...")
        
        try:
            # Run the RAG agent
            answer = await run_document_agent(
                session_id=f"eval-{i}",
                question=question
            )
            
            # Evaluate correctness (simple keyword matching for now)
            correctness = evaluate_correctness(answer, expected)
            
            # Evaluate relevance (check if answer is relevant to question)
            relevance = evaluate_relevance(answer, question)
            
            # Evaluate completeness (check if answer is complete)
            completeness = evaluate_completeness(answer, expected)
            
            result = {
                "question": question,
                "expected": expected,
                "actual": answer,
                "correctness": correctness,
                "relevance": relevance,
                "completeness": completeness,
                "context": context
            }
            
            results.append(result)
            
            print(f"  ✅ Correctness: {correctness:.2f}, Relevance: {relevance:.2f}, Completeness: {completeness:.2f}")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            results.append({
                "question": question,
                "expected": expected,
                "actual": f"ERROR: {str(e)}",
                "correctness": 0.0,
                "relevance": 0.0,
                "completeness": 0.0,
                "context": context
            })
    
    # Calculate aggregate metrics
    avg_correctness = sum(r["correctness"] for r in results) / len(results)
    avg_relevance = sum(r["relevance"] for r in results) / len(results)
    avg_completeness = sum(r["completeness"] for r in results) / len(results)
    
    print("\n" + "="*60)
    print("📈 Evaluation Summary")
    print("="*60)
    print(f"Total Test Cases: {len(results)}")
    print(f"Average Correctness: {avg_correctness:.2%}")
    print(f"Average Relevance: {avg_relevance:.2%}")
    print(f"Average Completeness: {avg_completeness:.2%}")
    print("="*60)
    
    # Save results to file
    with open("eval_results.json", "w") as f:
        json.dump({
            "summary": {
                "total": len(results),
                "avg_correctness": avg_correctness,
                "avg_relevance": avg_relevance,
                "avg_completeness": avg_completeness
            },
            "results": results
        }, f, indent=2)
    
    print("\n💾 Results saved to eval_results.json")
    
    return results


def evaluate_correctness(actual: str, expected: str) -> float:
    """
    Evaluate correctness by checking if key concepts from expected answer are present.
    Returns score between 0.0 and 1.0.
    """
    actual_lower = actual.lower()
    expected_lower = expected.lower()
    
    # Extract key words from expected answer (non-stop words)
    stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did", "will", "would", "should", "could", "may", "might", "must", "can"}
    
    expected_words = [w for w in expected_lower.split() if w not in stop_words and len(w) > 3]
    
    if not expected_words:
        return 0.0
    
    # Count how many key words appear in actual answer
    matches = sum(1 for word in expected_words if word in actual_lower)
    
    return matches / len(expected_words)


def evaluate_relevance(answer: str, question: str) -> float:
    """
    Evaluate if the answer is relevant to the question.
    Returns score between 0.0 and 1.0.
    """
    answer_lower = answer.lower()
    question_lower = question.lower()
    
    # Check if answer contains "I don't know" (not relevant)
    if "i don't know" in answer_lower or "don't know" in answer_lower:
        return 0.0
    
    # Extract key words from question
    question_words = [w for w in question_lower.split() if len(w) > 3]
    
    if not question_words:
        return 0.5  # Neutral if no key words
    
    # Check if answer mentions question keywords
    matches = sum(1 for word in question_words if word in answer_lower)
    
    return min(1.0, matches / len(question_words) * 2)  # Scale up


def evaluate_completeness(actual: str, expected: str) -> float:
    """
    Evaluate if the answer is complete (not too short, has substance).
    Returns score between 0.0 and 1.0.
    """
    # Check if answer is too short
    if len(actual) < 20:
        return 0.0
    
    # Check if answer is "I don't know"
    if "i don't know" in actual.lower():
        return 0.0
    
    # Check if answer has reasonable length compared to expected
    length_ratio = len(actual) / len(expected) if len(expected) > 0 else 0
    
    # Score based on length (too short = low, reasonable = high)
    if length_ratio < 0.3:
        return 0.3
    elif length_ratio < 0.6:
        return 0.6
    elif length_ratio < 1.5:
        return 1.0
    else:
        return 0.9  # Slightly penalize overly long answers


if __name__ == "__main__":
    # Run evaluation
    results = asyncio.run(run_evaluation())

