"""
Known Issues Templates for One-Click RCA

Predefined error patterns and queries for common issues.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

KNOWN_ISSUES: List[Dict[str, Any]] = [
    {
        "id": "auth_failures",
        "name": "Authentication Failures",
        "description": "401/403 authentication and authorization errors",
        "icon": "🔐",
        "query": "status=401 OR status=403",
        "search_type": "metadata",  # metadata, keyword, semantic
        "search_params": {
            "key": "status",
            "values": ["401", "403"],
        },
        "keywords": ["authentication", "authorization", "401", "403", "unauthorized", "forbidden"],
    },
    {
        "id": "otp_issues",
        "name": "OTP Issues",
        "description": "One-time password verification problems",
        "icon": "🔑",
        "query": "keyword: otp",
        "search_type": "keyword",
        "keywords": ["otp", "one-time password", "verification code", "2fa"],
    },
    {
        "id": "download_abuse",
        "name": "Download Abuse",
        "description": "Suspicious download patterns and abuse",
        "icon": "⬇️",
        "query": "endpoint contains /api/download/file",
        "search_type": "metadata",
        "search_params": {
            "key": "endpoint",
            "pattern": "/api/download/file",
        },
        "keywords": ["download", "file", "abuse", "rate limit"],
    },
    {
        "id": "db_timeouts",
        "name": "Database Timeouts",
        "description": "MySQL/database connection timeouts",
        "icon": "⏱️",
        "query": "timeout + mysql",
        "search_type": "semantic",
        "keywords": ["timeout", "mysql", "database", "connection", "query timeout"],
    },
    {
        "id": "slow_requests",
        "name": "Slow Requests",
        "description": "High latency requests (>3000ms)",
        "icon": "🐌",
        "query": "latency_ms > 3000",
        "search_type": "metadata",
        "search_params": {
            "key": "latency_ms",
            "operator": ">",
            "value": 3000,
        },
        "keywords": ["slow", "latency", "performance", "timeout"],
    },
]


def get_known_issue(issue_id: str) -> Optional[Dict[str, Any]]:
    """Get a known issue template by ID."""
    for issue in KNOWN_ISSUES:
        if issue["id"] == issue_id:
            return issue
    return None


def get_all_known_issues() -> List[Dict[str, Any]]:
    """Get all known issue templates."""
    return KNOWN_ISSUES.copy()


def build_query_for_issue(issue: Dict[str, Any]) -> str:
    """
    Build a search query from a known issue template.
    
    Args:
        issue: Known issue template dict
    
    Returns:
        Query string for error search
    """
    search_type = issue.get("search_type", "semantic")
    keywords = issue.get("keywords", [])
    
    if search_type == "keyword":
        # Use first keyword or combine
        return " ".join(keywords[:3])
    elif search_type == "metadata":
        # Build metadata-based query
        search_params = issue.get("search_params", {})
        if "values" in search_params:
            # Multiple values (OR)
            values = search_params["values"]
            return f"{search_params.get('key', 'status')} {' OR '.join(values)}"
        elif "pattern" in search_params:
            # Pattern match
            return f"{search_params.get('key', 'endpoint')} contains {search_params['pattern']}"
        elif "operator" in search_params:
            # Comparison operator
            return f"{search_params.get('key', 'latency_ms')} {search_params['operator']} {search_params.get('value', '')}"
        else:
            # Fallback to keywords
            return " ".join(keywords[:3])
    else:
        # Semantic search - use keywords
        return " ".join(keywords[:3])


def get_metadata_filters_for_issue(issue: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract metadata filters from a known issue template.
    
    Args:
        issue: Known issue template dict
    
    Returns:
        Dict with metadata filters or None
    """
    if issue.get("search_type") != "metadata":
        return None
    
    search_params = issue.get("search_params", {})
    if not search_params:
        return None
    
    # Build filter dict
    filters = {}
    
    if "values" in search_params:
        # OR condition: status in [401, 403]
        filters["status"] = search_params["values"]
    elif "pattern" in search_params:
        # Pattern match: endpoint contains pattern
        filters["endpoint"] = search_params.get("key", "endpoint")
        filters["pattern"] = search_params["pattern"]
    elif "operator" in search_params:
        # Comparison: latency_ms > 3000
        filters["latency_ms"] = search_params.get("key", "latency_ms")
        filters["operator"] = search_params["operator"]
        filters["value"] = search_params.get("value", 0)
    
    return filters if filters else None

