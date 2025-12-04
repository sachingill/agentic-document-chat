"""
LangSmith Evaluation Setup
Uses LangSmith's built-in evaluation framework for more sophisticated metrics
"""

import os
from langsmith import Client, aevaluate
from langchain_openai import ChatOpenAI
from app.agents.doc_agent import run_document_agent
import asyncio
from typing import Dict, Any

# Initialize LangSmith client
client = Client(api_key=os.getenv("LANGSMITH_API_KEY"))

# Test dataset
TEST_DATASET = [
    {
        "inputs": {"question": "How does circuit breaker protect A1?"},
        "outputs": {"expected": "Circuit breaker protects A1 by opening when A1 returns 521 error storms and returning 429 Too Many Requests."}
    },
    {
        "inputs": {"question": "What is SIM provisioning?"},
        "outputs": {"expected": "SIM provisioning is the process of activating and configuring a SIM card for use on a mobile network."}
    },
    {
        "inputs": {"question": "How does the billing system process subscription updates?"},
        "outputs": {"expected": "Billing systems use BSS (Business Support Systems) pipeline to process subscription updates."}
    },
    {
        "inputs": {"question": "What is API rate limiting?"},
        "outputs": {"expected": "API rate limiting prevents abuse and ensures fair resource allocation using token bucket algorithm."}
    },
    {
        "inputs": {"question": "How does connection pooling improve performance?"},
        "outputs": {"expected": "Database connection pooling improves performance by reusing database connections, reducing overhead."}
    }
]


async def rag_agent_predict(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Wrapper function for the RAG agent to be used in LangSmith evaluation.
    """
    question = inputs["question"]
    answer = await run_document_agent(session_id="eval", question=question)
    return {"output": answer}


async def evaluate_with_langsmith():
    """
    Run evaluation using LangSmith's evaluation framework.
    """
    print("🚀 Starting LangSmith Evaluation...")
    
    # Create dataset in LangSmith
    dataset_name = "rag-eval-dataset"
    
    try:
        # Create or get dataset
        dataset = client.create_dataset(
            dataset_name=dataset_name,
            description="RAG system evaluation dataset"
        )
        print(f"✅ Created dataset: {dataset_name}")
    except Exception:
        # Dataset might already exist
        dataset = client.read_dataset(dataset_name=dataset_name)
        print(f"✅ Using existing dataset: {dataset_name}")
    
    # Add examples to dataset
    for example in TEST_DATASET:
        try:
            client.create_example(
                inputs=example["inputs"],
                outputs=example["outputs"],
                dataset_id=dataset.id
            )
        except Exception:
            pass  # Example might already exist
    
    print(f"📊 Dataset ready with {len(TEST_DATASET)} examples\n")
    
    # Run evaluation with LangSmith (using aevaluate for async)
    try:
        results = await aevaluate(
            rag_agent_predict,
            data=dataset_name,
            evaluators=[
                # Using string-based evaluator names
                "correctness",  # Evaluates if answer is correct
                "helpfulness",  # Evaluates if answer is helpful
            ],
            experiment_prefix="rag-eval",
            max_concurrency=5,
        )
    except Exception as e:
        print(f"⚠️  Error with built-in evaluators: {e}")
        print("💡 Trying alternative approach without evaluators...")
        
        # Alternative: Use LangSmith's aevaluate without evaluators
        # This tracks runs but doesn't score them
        results = await aevaluate(
            rag_agent_predict,
            data=dataset_name,
            experiment_prefix="rag-eval",
            max_concurrency=5,
        )
    
    print("\n✅ Evaluation complete!")
    print(f"📊 View results at: https://smith.langchain.com")
    
    return results


if __name__ == "__main__":
    # Run evaluation
    asyncio.run(evaluate_with_langsmith())

