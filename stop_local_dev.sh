#!/bin/bash

# Stop Local Development Services

echo "🛑 Stopping Local Development Services"
echo "======================================"
echo ""

# Read PIDs from file
if [ -f "/tmp/rag_dev_pids.txt" ]; then
    PIDS=$(cat /tmp/rag_dev_pids.txt)
    echo "Found PIDs: $PIDS"
    
    for PID in $PIDS; do
        if ps -p $PID > /dev/null 2>&1; then
            echo "Stopping process $PID..."
            kill $PID 2>/dev/null
        fi
    done
    
    rm /tmp/rag_dev_pids.txt
    echo "✅ Stopped services from PID file"
else
    echo "⚠️  No PID file found, trying to find processes..."
fi

# Also try to kill by port
echo ""
echo "Checking ports..."

for PORT in 8000 8501; do
    PID=$(lsof -ti:$PORT 2>/dev/null)
    if [ -n "$PID" ]; then
        echo "Stopping process on port $PORT (PID: $PID)..."
        kill $PID 2>/dev/null
        sleep 1
        # Force kill if still running
        if lsof -ti:$PORT > /dev/null 2>&1; then
            kill -9 $PID 2>/dev/null
        fi
    fi
done

echo ""
echo "✅ All services stopped"
echo ""

