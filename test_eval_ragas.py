"""
Test RAGAS Evaluation
"""
import os
from dotenv import load_dotenv
load_dotenv()

import asyncio
from datasets import Dataset
from app.agents.doc_agent import run_document_agent
from app.agents.tools import retrieve_tool
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("=" * 70)
print("🧪 TEST 2: RAGAS Evaluation")
print("=" * 70)

# Check if RAGAS is installed
try:
    from ragas import evaluate
    from ragas.metrics import faithfulness, answer_relevancy, context_precision
    print("✅ RAGAS installed")
except ImportError:
    print("❌ RAGAS not installed")
    print("💡 Install with: pip install ragas datasets")
    exit(1)

# Check environment
openai_key = os.getenv("OPENAI_API_KEY")
if not openai_key:
    print("❌ OPENAI_API_KEY not found in .env file")
    exit(1)
else:
    print(f"✅ OPENAI_API_KEY found: {openai_key[:10]}...")

# Simple test dataset
TEST_CASES = [
    {
        "question": "What is SIM provisioning?",
        "ground_truth": "SIM provisioning is the process of activating and configuring a SIM card for use on a mobile network."
    },
    {
        "question": "How does circuit breaker protect A1?",
        "ground_truth": "Circuit breaker protects A1 by opening when A1 returns 521 error storms and returning 429 Too Many Requests."
    }
]

async def get_contexts_for_question(question: str, k: int = 5) -> list:
    """Retrieve contexts for a question"""
    try:
        result = retrieve_tool(question, k=k)
        contexts = result.get("results", [])
        return contexts if contexts else ["No context found"]
    except Exception as e:
        logger.error(f"Error retrieving contexts: {e}")
        return ["Error retrieving context"]

async def create_eval_dataset() -> Dataset:
    """Create evaluation dataset"""
    print("\n📊 Creating Evaluation Dataset...")
    
    questions = []
    answers = []
    contexts_list = []
    ground_truths = []
    
    for i, test_case in enumerate(TEST_CASES, 1):
        question = test_case["question"]
        ground_truth = test_case["ground_truth"]
        
        print(f"  [{i}/{len(TEST_CASES)}] Processing: {question[:50]}...")
        
        try:
            # Run RAG agent
            answer = await run_document_agent(
                session_id=f"ragas-eval-{i}",
                question=question
            )
            
            # Get contexts
            contexts = await get_contexts_for_question(question, k=5)
            
            questions.append(question)
            answers.append(answer)
            contexts_list.append(contexts)
            ground_truths.append(ground_truth)
            
            print(f"    ✅ Answer: {len(answer)} chars, Contexts: {len(contexts)}")
            
        except Exception as e:
            logger.error(f"    ❌ Error: {e}")
            questions.append(question)
            answers.append(f"ERROR: {str(e)}")
            contexts_list.append(["Error occurred"])
            ground_truths.append(ground_truth)
    
    dataset = Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts_list,
        "ground_truth": ground_truths
    })
    
    print(f"✅ Dataset created with {len(questions)} examples")
    return dataset

async def run_ragas_test():
    """Run RAGAS evaluation"""
    print("\n📈 Running RAGAS Evaluation...")
    print("   (This may take 1-2 minutes...)")
    
    # Create dataset
    dataset = await create_eval_dataset()
    
    # Run evaluation
    try:
        results = evaluate(
            dataset,
            metrics=[
                faithfulness,
                answer_relevancy,
                context_precision
            ]
        )
        
        print("\n✅ RAGAS Evaluation completed!")
        
        # Extract metrics
        metrics_df = results.to_pandas()
        
        print("\n📊 Results:")
        print("-" * 70)
        print(f"Faithfulness:      {metrics_df['faithfulness'].mean():.2%} (avg)")
        print(f"Answer Relevancy:  {metrics_df['answer_relevancy'].mean():.2%} (avg)")
        print(f"Context Precision: {metrics_df['context_precision'].mean():.2%} (avg)")
        print("-" * 70)
        
        # Save results
        metrics_df.to_csv("ragas_test_results.csv", index=False)
        print("\n💾 Results saved to: ragas_test_results.csv")
        
        print("\n" + "=" * 70)
        print("✅ RAGAS Evaluation Test: PASSED")
        print("=" * 70)
        
        return results
        
    except Exception as e:
        print(f"\n❌ RAGAS Evaluation error: {e}")
        print("\n💡 Common issues:")
        print("   1. Make sure documents are ingested first")
        print("   2. Check OPENAI_API_KEY is correct")
        print("   3. Verify RAGAS is installed: pip install ragas datasets")
        print("\n" + "=" * 70)
        print("❌ RAGAS Evaluation Test: FAILED")
        print("=" * 70)
        raise

if __name__ == "__main__":
    asyncio.run(run_ragas_test())

