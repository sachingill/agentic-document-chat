#!/bin/bash

# Test script to verify all servers are accessible

echo "🔍 Testing Server Connections..."
echo ""

# Test Structured RAG (Port 8000)
echo "1. Testing Structured RAG API (port 8000)..."
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "   ✅ Structured RAG API is running"
    curl -s http://localhost:8000/ | python -m json.tool 2>/dev/null || curl -s http://localhost:8000/
else
    echo "   ❌ Structured RAG API is NOT running"
    echo "   Start it with: uvicorn app.main:app --reload --port 8000"
fi

echo ""

# Test Agentic RAG (Port 8001)
echo "2. Testing Agentic RAG API (port 8001)..."
if curl -s http://localhost:8001/ > /dev/null 2>&1; then
    echo "   ✅ Agentic RAG API is running"
    curl -s http://localhost:8001/ | python -m json.tool 2>/dev/null || curl -s http://localhost:8001/
else
    echo "   ❌ Agentic RAG API is NOT running"
    echo "   Start it with: cd agentic && uvicorn app.main:app --reload --port 8001"
fi

echo ""
echo "3. Testing Streamlit..."
if command -v streamlit &> /dev/null; then
    echo "   ✅ Streamlit is installed"
    streamlit --version
else
    echo "   ❌ Streamlit is NOT installed"
    echo "   Install with: pip install streamlit requests"
fi

echo ""
echo "Done! 🎉"

