#!/bin/bash
# Test runner script for the API project

set -e

echo "🧪 Running Test Suite"
echo "===================="
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run tests with coverage
echo "Running all tests with coverage..."
pytest --cov=app --cov-report=term-missing --cov-report=html -v

echo ""
echo "✅ Tests completed!"
echo "📊 Coverage report generated in htmlcov/index.html"


