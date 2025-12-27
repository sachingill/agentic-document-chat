"""
Rate Limiting Configuration for FastAPI

Supports multiple rate limiting strategies:
1. In-memory (default) - Simple, no dependencies
2. Redis (optional) - Distributed, production-ready

Usage:
    from app.rate_limiter import limiter, get_rate_limiter
    
    @app.get("/")
    @limiter.limit("10/minute")
    async def root(request: Request):
        return {"message": "Hello"}
"""
import os
from typing import Optional
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request

# Rate limiting configuration from environment variables
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
RATE_LIMIT_DEFAULT = os.getenv("RATE_LIMIT_DEFAULT", "100/hour")  # Default rate limit
RATE_LIMIT_STORAGE_URI = os.getenv("RATE_LIMIT_STORAGE_URI", None)  # Redis URI if using Redis

# Per-endpoint rate limits (can be overridden)
RATE_LIMITS = {
    "default": os.getenv("RATE_LIMIT_DEFAULT", "100/hour"),
    "chat": os.getenv("RATE_LIMIT_CHAT", "20/minute"),  # Chat endpoints are more resource-intensive
    "ingest": os.getenv("RATE_LIMIT_INGEST", "10/minute"),  # Ingest endpoints are expensive
    "predict": os.getenv("RATE_LIMIT_PREDICT", "30/minute"),
    "root": os.getenv("RATE_LIMIT_ROOT", "100/hour"),
}


def get_rate_limiter_key_func(request: Request) -> str:
    """
    Custom key function for rate limiting.
    
    Uses client IP address by default.
    Can be extended to use API keys, user IDs, etc.
    """
    # Try to get API key from header
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"api_key:{api_key}"
    
    # Try to get user ID from header
    user_id = request.headers.get("X-User-ID")
    if user_id:
        return f"user_id:{user_id}"
    
    # Fall back to IP address
    return get_remote_address(request)


def create_limiter(storage_uri: Optional[str] = None) -> Limiter:
    """
    Create a rate limiter instance.
    
    Args:
        storage_uri: Optional Redis URI (e.g., "redis://localhost:6379")
                    If None, uses in-memory storage
    
    Returns:
        Limiter instance
    """
    if storage_uri:
        # Use Redis for distributed rate limiting
        try:
            from slowapi.middleware import SlowAPIMiddleware
            limiter = Limiter(
                key_func=get_rate_limiter_key_func,
                storage_uri=storage_uri,
                default_limits=[RATE_LIMIT_DEFAULT],
            )
            print(f"✅ Rate limiter initialized with Redis: {storage_uri}")
            return limiter
        except ImportError:
            print("⚠️  Redis not available, falling back to in-memory storage")
            # Fall through to in-memory
    
    # Use in-memory storage (default)
    limiter = Limiter(
        key_func=get_rate_limiter_key_func,
        default_limits=[RATE_LIMIT_DEFAULT] if RATE_LIMIT_ENABLED else [],
    )
    if RATE_LIMIT_ENABLED:
        print(f"✅ Rate limiter initialized (in-memory, default: {RATE_LIMIT_DEFAULT})")
    else:
        print("⚠️  Rate limiting is disabled")
    return limiter


# Create the global limiter instance
limiter = create_limiter(RATE_LIMIT_STORAGE_URI)


def get_rate_limit_for_endpoint(endpoint_name: str) -> str:
    """
    Get the rate limit string for a specific endpoint.
    
    Args:
        endpoint_name: Name of the endpoint (e.g., "chat", "ingest")
    
    Returns:
        Rate limit string (e.g., "20/minute")
    """
    return RATE_LIMITS.get(endpoint_name, RATE_LIMITS["default"])


def setup_rate_limiter(app):
    """
    Set up rate limiting middleware and error handler for FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    if not RATE_LIMIT_ENABLED:
        print("⚠️  Rate limiting is disabled (set RATE_LIMIT_ENABLED=true to enable)")
        return
    
    # Add rate limit error handler
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    # Add middleware (if using Redis)
    if RATE_LIMIT_STORAGE_URI:
        from slowapi.middleware import SlowAPIMiddleware
        app.add_middleware(SlowAPIMiddleware)






