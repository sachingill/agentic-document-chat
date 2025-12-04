"""
Test LangSmith Evaluation
"""
import os
from dotenv import load_dotenv
load_dotenv()

import asyncio
from langsmith import Client, aevaluate
from app.agents.doc_agent import run_document_agent
from typing import Dict, Any

print("=" * 70)
print("🧪 TEST 1: LangSmith Evaluation")
print("=" * 70)

# Check environment
api_key = os.getenv("LANGSMITH_API_KEY")
if not api_key:
    print("❌ LANGSMITH_API_KEY not found in .env file")
    exit(1)
else:
    print(f"✅ LANGSMITH_API_KEY found: {api_key[:10]}...")

openai_key = os.getenv("OPENAI_API_KEY")
if not openai_key:
    print("❌ OPENAI_API_KEY not found in .env file")
    exit(1)
else:
    print(f"✅ OPENAI_API_KEY found: {openai_key[:10]}...")

# Initialize client
try:
    client = Client(api_key=api_key)
    print("✅ LangSmith Client initialized")
except Exception as e:
    print(f"❌ Error initializing client: {e}")
    exit(1)

# Test dataset creation
print("\n📊 Testing Dataset Creation...")
dataset_name = "rag-eval-test"

try:
    dataset = client.create_dataset(
        dataset_name=dataset_name,
        description="Test dataset for RAG evaluation"
    )
    print(f"✅ Created dataset: {dataset_name}")
except Exception as e:
    if "already exists" in str(e).lower() or "409" in str(e):
        dataset = client.read_dataset(dataset_name=dataset_name)
        print(f"✅ Using existing dataset: {dataset_name}")
    else:
        print(f"❌ Error creating dataset: {e}")
        exit(1)

# Add test example
print("\n➕ Adding Test Example...")
try:
    client.create_example(
        inputs={"question": "What is SIM provisioning?"},
        outputs={"expected": "SIM provisioning is the process of activating a SIM card."},
        dataset_id=dataset.id
    )
    print("✅ Test example added")
except Exception as e:
    if "already exists" in str(e).lower() or "409" in str(e):
        print("✅ Test example already exists")
    else:
        print(f"⚠️  Warning: {e}")

# Test RAG function
print("\n🤖 Testing RAG Agent Function...")
async def test_rag_function(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Test wrapper for RAG agent"""
    question = inputs["question"]
    try:
        answer = await run_document_agent(session_id="test", question=question)
        return {"output": answer}
    except Exception as e:
        return {"output": f"ERROR: {str(e)}"}

# Test single call
try:
    test_result = asyncio.run(test_rag_function({"question": "What is SIM provisioning?"}))
    print(f"✅ RAG function works: {len(test_result['output'])} chars returned")
    if "ERROR" in test_result['output']:
        print(f"   ⚠️  Error in RAG: {test_result['output']}")
except Exception as e:
    print(f"❌ RAG function error: {e}")
    exit(1)

# Test evaluation
print("\n📈 Running LangSmith Evaluation...")
print("   (This may take 1-2 minutes...)")

async def run_evaluation():
    try:
        results = await aevaluate(
            test_rag_function,
            data=dataset_name,
            experiment_prefix="rag-test",
            max_concurrency=1,
        )
        return results
    except Exception as e:
        raise e

try:
    results = asyncio.run(run_evaluation())
    print("\n✅ Evaluation completed successfully!")
    print(f"📊 View results at: https://smith.langchain.com")
    print("\n" + "=" * 70)
    print("✅ LangSmith Evaluation Test: PASSED")
    print("=" * 70)
except Exception as e:
    print(f"\n❌ Evaluation error: {e}")
    print("\n💡 Common issues:")
    print("   1. Check LANGSMITH_API_KEY is correct")
    print("   2. Ensure you have internet connection")
    print("   3. Verify dataset exists in LangSmith")
    print("\n" + "=" * 70)
    print("❌ LangSmith Evaluation Test: FAILED")
    print("=" * 70)
    exit(1)

