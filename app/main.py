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

# Validate OpenAI API key is set
if not os.getenv('OPENAI_API_KEY'):
    raise ValueError(
        "OPENAI_API_KEY not found in environment. "
        "Please set it as an environment variable on your hosting platform."
    )

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import user, predict
from app.routers.agent import router as agent_router
import logging

# Configure logging to see debug messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)



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

app.include_router(user.router)
# Register routers
app.include_router(predict.router)

app.include_router(agent_router)

@app.get("/")
async def root():
    return {"message": "API is running"}