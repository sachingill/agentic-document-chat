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

# Load environment variables from .env file (only for local development)
# In production, environment variables should be set on the hosting platform
parent_dir = Path(__file__).parent.parent.parent
env_path = parent_dir / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

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
        "Please set it as an environment variable on your hosting platform."
    )

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

# Add CORS middleware for production deployment
# Allows Streamlit UI (hosted separately) to access this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

