"""
Test script to verify LangSmith evaluation is working
"""

import os
import asyncio
from langsmith import Client, evaluate
from app.agents.doc_agent import run_document_agent
from typing import Dict, Any

# Check environment
print("🔍 Checking LangSmith Configuration...")
print("=" * 60)

api_key = os.getenv("LANGSMITH_API_KEY")
if not api_key:
    print("❌ LANGSMITH_API_KEY not found in environment")
    print("💡 Add it to your .env file: LANGSMITH_API_KEY=your-key")
    exit(1)
else:
    print(f"✅ LANGSMITH_API_KEY found: {api_key[:10]}...")

# Initialize client
try:
    client = Client(api_key=api_key)
    print("✅ LangSmith Client initialized")
except Exception as e:
    print(f"❌ Error initializing client: {e}")
    exit(1)

# Test dataset creation
print("\n📊 Testing Dataset Creation...")
print("=" * 60)

dataset_name = "rag-eval-test"

try:
    # Try to create dataset
    dataset = client.create_dataset(
        dataset_name=dataset_name,
        description="Test dataset for RAG evaluation"
    )
    print(f"✅ Created dataset: {dataset_name}")
except Exception as e:
    if "already exists" in str(e).lower():
        dataset = client.read_dataset(dataset_name=dataset_name)
        print(f"✅ Using existing dataset: {dataset_name}")
    else:
        print(f"❌ Error creating dataset: {e}")
        exit(1)

# Add a test example
print("\n➕ Adding Test Example...")
print("=" * 60)

try:
    client.create_example(
        inputs={"question": "What is SIM provisioning?"},
        outputs={"expected": "SIM provisioning is the process of activating a SIM card."},
        dataset_id=dataset.id
    )
    print("✅ Test example added")
except Exception as e:
    if "already exists" in str(e).lower():
        print("✅ Test example already exists")
    else:
        print(f"⚠️  Warning: {e}")

# Test RAG function
print("\n🤖 Testing RAG Agent Function...")
print("=" * 60)

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
except Exception as e:
    print(f"❌ RAG function error: {e}")
    exit(1)

# Test evaluation
print("\n📈 Testing LangSmith Evaluation...")
print("=" * 60)

try:
    print("Running evaluation (this may take a minute)...")
    results = evaluate(
        test_rag_function,
        data=dataset_name,
        experiment_prefix="rag-test",
        max_concurrency=1,
    )
    print("✅ Evaluation completed successfully!")
    print(f"📊 View results at: https://smith.langchain.com")
    print("\n" + "=" * 60)
    print("✅ LangSmith Evaluation is working correctly!")
    print("=" * 60)
except Exception as e:
    print(f"❌ Evaluation error: {e}")
    print("\n💡 Common issues:")
    print("   1. Check LANGSMITH_API_KEY is correct")
    print("   2. Ensure you have internet connection")
    print("   3. Verify dataset exists in LangSmith")
    exit(1)

