#!/bin/bash

# RAG Chat UI Startup Script
# This script helps you start all services needed for the UI

echo "🚀 Starting RAG Chat UI Services..."
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Virtual environment not detected. Activating..."
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        echo "❌ Virtual environment not found. Please create one first:"
        echo "   python -m venv venv"
        echo "   source venv/bin/activate"
        exit 1
    fi
fi

# Check if Streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "📦 Installing Streamlit..."
    pip install streamlit requests
fi

# Check if servers are running
echo "🔍 Checking API servers..."

# Check Structured RAG (port 8000)
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "✅ Structured RAG API is running on port 8000"
else
    echo "⚠️  Structured RAG API is not running on port 8000"
    echo "   Start it with: uvicorn app.main:app --reload --port 8000"
fi

# Check Agentic RAG (port 8001)
if curl -s http://localhost:8001/ > /dev/null 2>&1; then
    echo "✅ Agentic RAG API is running on port 8001"
else
    echo "⚠️  Agentic RAG API is not running on port 8001"
    echo "   Start it with: cd agentic && uvicorn app.main:app --reload --port 8001"
fi

echo ""
echo "🎨 Starting Streamlit UI..."
echo "   UI will open at: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the UI"
echo ""

streamlit run ui.py

