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
    
    LangSmith provides:
    - Tracing: Track all LLM calls, tool invocations, and agent steps
    - Monitoring: Performance metrics, latency, token usage
    - Debugging: Inspect prompts, responses, and intermediate states
    - Evaluation: Test and compare different prompts/models
    """
    
    # LangSmith API Key (get from https://smith.langchain.com/settings)
    API_KEY = os.getenv("LANGSMITH_API_KEY", "")
    
    # LangSmith endpoint (default is cloud, can be self-hosted)
    ENDPOINT = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
    
    # Enable/disable tracing (set to "true" to enable)
    TRACING = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
    
    # Project name for organizing traces in LangSmith dashboard
    PROJECT_NAME = os.getenv("LANGSMITH_PROJECT", "rag-api")
    
    # Tags for filtering traces (comma-separated)
    TAGS = os.getenv("LANGSMITH_TAGS", "production,rag").split(",") if os.getenv("LANGSMITH_TAGS") else []
    
    @classmethod
    def is_enabled(cls) -> bool:
        """Check if LangSmith tracing is enabled."""
        return cls.TRACING and bool(cls.API_KEY)
    
    @classmethod
    def setup_environment(cls):
        """
        Set up environment variables for LangSmith.
        This is called automatically when the module is imported.
        """
        if cls.is_enabled():
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_ENDPOINT"] = cls.ENDPOINT
            os.environ["LANGCHAIN_API_KEY"] = cls.API_KEY
            os.environ["LANGCHAIN_PROJECT"] = cls.PROJECT_NAME
            
            if cls.TAGS:
                os.environ["LANGCHAIN_TAGS"] = ",".join(cls.TAGS)
            
            print(f"✅ LangSmith tracing enabled for project: {cls.PROJECT_NAME}")
        else:
            print("⚠️  LangSmith tracing disabled (set LANGSMITH_TRACING=true and LANGSMITH_API_KEY)")


# Auto-setup when module is imported
LangSmithConfig.setup_environment()

