from dotenv import load_dotenv
import os

# Load environment variables from .env file (only for local development)
# In production, environment variables should be set on the hosting platform
# This allows .env to work locally but doesn't require it in production
if os.path.exists('.env'):
    load_dotenv()

# Import LangSmith config early to set up tracing
# This must be imported BEFORE any LangChain/LangGraph imports
from app.config import LangSmithConfig

from app.core.settings import Settings

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys
from pathlib import Path
from app.api.router import api_router
from app.core.logging import configure_logging

# Add project root to path for multiagent imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logger = configure_logging(logging.INFO)

settings = Settings()
settings.validate()



app = FastAPI (
    title="API",
    version="0.1.0",
    description="API for the project",
    contact={
        "name": "API Support",
        "url": "https://www.google.com",
        "email": "support@example.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
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

app.include_router(api_router)

@app.get("/")
async def root():
    return {"message": "API is running"}