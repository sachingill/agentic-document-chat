#!/bin/bash

# Local Development Startup Script
# Starts all services needed for local development

echo "🚀 Starting Local Development Environment"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "   Create it with: python -m venv venv"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found"
    echo "   Creating from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "   ✅ Created .env file"
        echo "   ⚠️  Please add your OPENAI_API_KEY to .env"
    else
        echo "   ❌ .env.example not found either"
        echo "   Please create .env file with OPENAI_API_KEY"
    fi
fi

# Check if OPENAI_API_KEY is set
if ! grep -q "OPENAI_API_KEY" .env 2>/dev/null || grep -q "OPENAI_API_KEY=your-" .env 2>/dev/null; then
    echo "⚠️  OPENAI_API_KEY not set in .env"
    echo "   Please add your OpenAI API key to .env file"
fi

echo ""
echo "📋 Starting Services..."
echo ""

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Check ports
PORTS_IN_USE=0
if check_port 8000; then
    echo "⚠️  Port 8000 is already in use (Backend API)"
    PORTS_IN_USE=1
fi

if check_port 8501; then
    echo "⚠️  Port 8501 is already in use (Streamlit UI)"
    PORTS_IN_USE=1
fi

if [ $PORTS_IN_USE -eq 1 ]; then
    echo ""
    echo "❌ Some ports are already in use"
    echo "   Kill existing processes or use different ports"
    echo ""
    echo "To kill processes on ports:"
    echo "   lsof -ti:8000 | xargs kill -9"
    echo "   lsof -ti:8501 | xargs kill -9"
    exit 1
fi

echo "✅ All ports are free"
echo ""

# Start Backend API (single server) in background
echo "1️⃣  Starting Backend API (port 8000)..."
cd /Users/sachin/nltk_data/api
uvicorn app.main:app --reload --port 8000 > /tmp/api.log 2>&1 &
API_PID=$!
echo "   ✅ Started (PID: $API_PID)"
echo "   📝 Logs: /tmp/api.log"

# Wait a bit for it to start
sleep 2

# Start Streamlit UI in background
echo ""
echo "2️⃣  Starting Streamlit UI (port 8501)..."
cd /Users/sachin/nltk_data/api
streamlit run ui.py --server.headless=true > /tmp/streamlit_ui.log 2>&1 &
STREAMLIT_PID=$!
echo "   ✅ Started (PID: $STREAMLIT_PID)"
echo "   📝 Logs: /tmp/streamlit_ui.log"

# Wait for services to start
echo ""
echo "⏳ Waiting for services to start..."
sleep 5

# Verify services
echo ""
echo "🔍 Verifying services..."
echo ""

# Check Structured API
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "✅ Backend API is running on http://localhost:8000"
else
    echo "❌ Backend API failed to start"
    echo "   Check logs: tail -f /tmp/api.log"
fi

# Check Streamlit
if curl -s http://localhost:8501/ > /dev/null 2>&1; then
    echo "✅ Streamlit UI is running on http://localhost:8501"
else
    echo "⚠️  Streamlit UI might still be starting..."
    echo "   Check logs: tail -f /tmp/streamlit_ui.log"
fi

echo ""
echo "=========================================="
echo "🎉 Local Development Environment Ready!"
echo "=========================================="
echo ""
echo "📍 Services:"
echo "   - Backend API:  http://localhost:8000"
echo "   - Streamlit UI:       http://localhost:8501"
echo ""
echo "📝 View logs:"
echo "   - API:        tail -f /tmp/api.log"
echo "   - Streamlit UI:   tail -f /tmp/streamlit_ui.log"
echo ""
echo "🛑 Stop all services:"
echo "   kill $API_PID $STREAMLIT_PID"
echo ""
echo "   Or use: ./stop_local_dev.sh"
echo ""

# Save PIDs to file for easy stopping
echo "$API_PID $STREAMLIT_PID" > /tmp/rag_dev_pids.txt

# Keep script running (services run in background)
echo "Services are running in the background."
echo "Press Ctrl+C to exit (services will keep running)"
echo ""

# Wait for user interrupt
trap "echo ''; echo 'Script exited. Services are still running.'; echo 'Use ./stop_local_dev.sh to stop them.'; exit" INT
wait

