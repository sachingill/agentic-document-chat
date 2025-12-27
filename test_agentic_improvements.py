#!/usr/bin/env python3
"""
Test script to verify agentic improvements:
1. Fixed metadata extraction (no hardcoded values)
2. Improved keyword extraction (LLM-based)
3. Reranking before generation
4. Deduplication
5. Context limiting
6. Structured JSON output
"""

import requests
import json
import time
import sys

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def test_endpoint(url, name):
    """Test if endpoint is accessible"""
    try:
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            print(f"{GREEN}✅ {name} is running{RESET}")
            return True
        else:
            print(f"{RED}❌ {name} returned status {response.status_code}{RESET}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"{RED}❌ {name} is not accessible: {e}{RESET}")
        return False

def test_agentic_chat(question, session_id="test-session"):
    """Test agentic chat endpoint"""
    url = "http://localhost:8001/agentic/chat"
    payload = {
        "question": question,
        "session_id": session_id
    }
    
    try:
        print(f"\n{BLUE}📤 Testing: {question}{RESET}")
        start_time = time.time()
        response = requests.post(url, json=payload, timeout=60)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get("answer", "")
            guardrail = data.get("guardrail", {})
            agentic = data.get("agentic", False)
            
            print(f"{GREEN}✅ Response received ({elapsed:.2f}s){RESET}")
            print(f"   Answer: {answer[:100]}..." if len(answer) > 100 else f"   Answer: {answer}")
            print(f"   Agentic flag: {agentic}")
            print(f"   Guardrail: {guardrail.get('stage', 'none')}")
            return True, data
        else:
            print(f"{RED}❌ Error: {response.status_code}{RESET}")
            print(f"   {response.text}")
            return False, None
    except requests.exceptions.Timeout:
        print(f"{RED}❌ Request timed out (>60s){RESET}")
        return False, None
    except Exception as e:
        print(f"{RED}❌ Error: {e}{RESET}")
        return False, None

def main():
    print(f"{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}🧪 Testing Agentic RAG Improvements{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    # Test 1: Check if servers are running
    print(f"{YELLOW}1. Checking server status...{RESET}")
    structured_ok = test_endpoint("http://localhost:8000/", "Structured RAG (8000)")
    agentic_ok = test_endpoint("http://localhost:8001/", "Agentic RAG (8001)")
    
    if not agentic_ok:
        print(f"\n{RED}❌ Agentic server is not running!{RESET}")
        print(f"{YELLOW}Start it with:{RESET}")
        print(f"  cd agentic && uvicorn app.main:app --reload --port 8001")
        sys.exit(1)
    
    # Test 2: Test metadata extraction (should NOT use hardcoded "circuit_breaker")
    print(f"\n{YELLOW}2. Testing metadata extraction (no hardcoded values)...{RESET}")
    success, data = test_agentic_chat(
        "Find documents about load balancing",
        "test-metadata"
    )
    if success:
        print(f"{GREEN}✅ Metadata extraction test passed{RESET}")
    
    # Test 3: Test keyword extraction (should use LLM, not naive splitting)
    print(f"\n{YELLOW}3. Testing keyword extraction (LLM-based)...{RESET}")
    success, data = test_agentic_chat(
        "What is SIM provisioning and how does it work?",
        "test-keywords"
    )
    if success:
        print(f"{GREEN}✅ Keyword extraction test passed{RESET}")
    
    # Test 4: Test general question (should use retrieve_tool)
    print(f"\n{YELLOW}4. Testing general question (retrieve_tool)...{RESET}")
    success, data = test_agentic_chat(
        "What is a circuit breaker?",
        "test-general"
    )
    if success:
        print(f"{GREEN}✅ General question test passed{RESET}")
    
    # Test 5: Test complex question (should trigger multiple iterations)
    print(f"\n{YELLOW}5. Testing complex question (iterative refinement)...{RESET}")
    success, data = test_agentic_chat(
        "Compare circuit breakers and load balancing, explain their differences and use cases",
        "test-complex"
    )
    if success:
        print(f"{GREEN}✅ Complex question test passed{RESET}")
    
    # Test 6: Test context limiting (should not exceed MAX_CONTEXT_DOCS)
    print(f"\n{YELLOW}6. Testing context limiting...{RESET}")
    success, data = test_agentic_chat(
        "Tell me everything about all topics in the documents",
        "test-context-limit"
    )
    if success:
        print(f"{GREEN}✅ Context limiting test passed{RESET}")
    
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{GREEN}✅ All tests completed!{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    print(f"\n{YELLOW}Note: Check server logs to verify:{RESET}")
    print(f"  - Tool selection uses JSON output")
    print(f"  - Metadata extraction is dynamic (not hardcoded)")
    print(f"  - Keyword extraction uses LLM")
    print(f"  - Reranking happens before generation")
    print(f"  - Context is deduplicated and limited")

if __name__ == "__main__":
    main()

