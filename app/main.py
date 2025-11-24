from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Import LangSmith config early to set up tracing
# This must be imported BEFORE any LangChain/LangGraph imports
from app.config import LangSmithConfig

# Validate OpenAI API key is set
if not os.getenv('OPENAI_API_KEY'):
    raise ValueError(
        "OPENAI_API_KEY not found in environment. "
        "Please set it in .env file or as an environment variable."
    )

from fastapi import FastAPI
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


app.include_router(user.router)
# Register routers
app.include_router(predict.router)

app.include_router(agent_router)

@app.get("/")
async def root():
    return {"message": "API is running"}