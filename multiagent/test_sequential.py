"""
Test script for Sequential Multi-Agent workflow
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from multiagent.app.agents.sequential_agent import run_sequential_agent


def test_sequential_workflow():
    """Test the sequential multi-agent workflow."""
    
    print("=" * 60)
    print("Testing Sequential Multi-Agent Workflow")
    print("=" * 60)
    
    # Test 1: Simple question
    print("\n📝 Test 1: Simple Question")
    print("-" * 60)
    question1 = "What is a circuit breaker?"
    print(f"Question: {question1}")
    
    result1 = run_sequential_agent(
        question=question1,
        session_id="test_1"
    )
    
    print(f"\n✅ Answer ({len(result1['answer'])} chars):")
    print(result1["answer"][:200] + "..." if len(result1["answer"]) > 200 else result1["answer"])
    print(f"\n⏱️  Execution time: {result1['execution_time']:.2f}s")
    print(f"📊 Metadata: {result1.get('metadata', {})}")
    
    # Test 2: Complex question
    print("\n\n📝 Test 2: Complex Question")
    print("-" * 60)
    question2 = "Compare circuit breakers and load balancing, explain their differences"
    print(f"Question: {question2}")
    
    result2 = run_sequential_agent(
        question=question2,
        session_id="test_2"
    )
    
    print(f"\n✅ Answer ({len(result2['answer'])} chars):")
    print(result2["answer"][:200] + "..." if len(result2["answer"]) > 200 else result2["answer"])
    print(f"\n⏱️  Execution time: {result2['execution_time']:.2f}s")
    print(f"📊 Metadata: {result2.get('metadata', {})}")
    
    print("\n" + "=" * 60)
    print("✅ All tests complete!")
    print("=" * 60)


if __name__ == "__main__":
    test_sequential_workflow()

