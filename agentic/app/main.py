"""
AGENTIC RAG API - Main Application

This is the agentic version with:
- LLM-based tool selection
- Conditional routing
- Iterative refinement
"""

from dotenv import load_dotenv
import os
import sys
from pathlib import Path

# Load environment variables from parent directory
parent_dir = Path(__file__).parent.parent.parent
load_dotenv(dotenv_path=parent_dir / ".env")

# Add agentic directory to path (two levels up from main.py)
# main.py is at: agentic/app/main.py
# Need: agentic/ (so that "from app.xxx" imports work)
agentic_dir = Path(__file__).parent.parent
sys.path.insert(0, str(agentic_dir))

# Import LangSmith config early
from app.config import LangSmithConfig

# Validate OpenAI API key
if not os.getenv('OPENAI_API_KEY'):
    raise ValueError(
        "OPENAI_API_KEY not found in environment. "
        "Please set it in .env file or as an environment variable."
    )

from fastapi import FastAPI
import logging

# Import router
from app.routers.agentic_agent import router as agentic_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(
    title="Agentic RAG API",
    version="0.2.0",
    description="Fully agentic RAG system with dynamic tool selection and conditional routing",
)

# Register agentic router
app.include_router(agentic_router)

@app.get("/")
async def root():
    return {
        "message": "Agentic RAG API is running",
        "version": "agentic",
        "endpoints": {
            "chat": "/agentic/chat",
            "ingest": "/agentic/ingest/json"
        }
    }

