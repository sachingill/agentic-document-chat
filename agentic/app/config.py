"""
Configuration module for LangSmith observability and other settings.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class LangSmithConfig:
    """
    LangSmith configuration for observability.
    """
    
    API_KEY = os.getenv("LANGSMITH_API_KEY", "")
    ENDPOINT = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
    TRACING = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
    PROJECT_NAME = os.getenv("LANGSMITH_PROJECT", "rag-api-agentic")
    TAGS = os.getenv("LANGSMITH_TAGS", "production,rag,agentic").split(",") if os.getenv("LANGSMITH_TAGS") else []
    
    @classmethod
    def is_enabled(cls) -> bool:
        """Check if LangSmith tracing is enabled."""
        return cls.TRACING and bool(cls.API_KEY)
    
    @classmethod
    def setup_environment(cls):
        """Set up environment variables for LangSmith."""
        if cls.is_enabled():
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_ENDPOINT"] = cls.ENDPOINT
            os.environ["LANGCHAIN_API_KEY"] = cls.API_KEY
            os.environ["LANGCHAIN_PROJECT"] = cls.PROJECT_NAME
            
            if cls.TAGS:
                os.environ["LANGCHAIN_TAGS"] = ",".join(cls.TAGS)
            
            print(f"✅ LangSmith tracing enabled for project: {cls.PROJECT_NAME}")
        else:
            print("⚠️  LangSmith tracing disabled")


# Auto-setup when module is imported
LangSmithConfig.setup_environment()

