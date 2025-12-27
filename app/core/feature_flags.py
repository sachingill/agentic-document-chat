"""
Feature Flag System with Tenant-Based Configuration

Supports tenant-specific feature flags for multi-tenancy.
Features can be enabled/disabled per tenant via configuration.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from starlette.requests import Request


# Default feature flags (all enabled for default tenant)
DEFAULT_FEATURES = {
    "rca_chat": True,
    "rca_ingest": True,
    "structured_rag": True,
    "agentic_rag": True,
    "multiagent_rag": True,
    "knowledge_base": True,
    "feedback": True,
}

# Feature flag configuration file path
FEATURE_FLAGS_CONFIG_PATH = os.getenv(
    "FEATURE_FLAGS_CONFIG_PATH",
    str(Path(__file__).parent.parent.parent / "feature_flags.json"),
)


class FeatureFlags:
    """
    Manages feature flags per tenant.
    
    Configuration format (JSON):
    {
        "default": {
            "rca_chat": true,
            "rca_ingest": true,
            ...
        },
        "tenant_1": {
            "rca_chat": true,
            "rca_ingest": false,
            ...
        },
        "tenant_2": {
            "rca_chat": false,
            ...
        }
    }
    """

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or FEATURE_FLAGS_CONFIG_PATH
        self._config: Dict[str, Dict[str, bool]] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load feature flag configuration from file or environment."""
        # Try to load from file
        config_file = Path(self.config_path)
        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    self._config = json.load(f)
                return
            except Exception as e:
                print(f"Warning: Failed to load feature flags from {config_file}: {e}")

        # Fallback: load from environment variable
        env_config = os.getenv("FEATURE_FLAGS_CONFIG")
        if env_config:
            try:
                self._config = json.loads(env_config)
                return
            except Exception:
                pass

        # Default: use default features for all tenants
        self._config = {"default": DEFAULT_FEATURES.copy()}

    def reload(self) -> None:
        """Reload configuration from file."""
        self._load_config()

    def is_enabled(self, feature: str, tenant: Optional[str] = None) -> bool:
        """
        Check if a feature is enabled for a tenant.
        
        Args:
            feature: Feature name (e.g., "rca_chat")
            tenant: Tenant ID (optional, defaults to "default")
        
        Returns:
            True if feature is enabled, False otherwise
        """
        tenant = tenant or "default"

        # Check tenant-specific config
        if tenant in self._config:
            tenant_config = self._config[tenant]
            if feature in tenant_config:
                return tenant_config[feature]

        # Fallback to default tenant
        if "default" in self._config:
            default_config = self._config["default"]
            if feature in default_config:
                return default_config[feature]

        # If feature not found, default to False (safe default)
        return False

    def get_tenant_features(self, tenant: Optional[str] = None) -> Dict[str, bool]:
        """
        Get all feature flags for a tenant.
        
        Args:
            tenant: Tenant ID (optional, defaults to "default")
        
        Returns:
            Dict of feature names to enabled status
        """
        tenant = tenant or "default"
        features = DEFAULT_FEATURES.copy()

        # Merge tenant-specific config
        if tenant in self._config:
            features.update(self._config[tenant])
        elif "default" in self._config:
            features.update(self._config["default"])

        return features

    def get_config(self) -> Dict[str, Dict[str, bool]]:
        """Get the full configuration."""
        return self._config.copy()


# Global feature flags instance
_feature_flags: Optional[FeatureFlags] = None


def get_feature_flags() -> FeatureFlags:
    """Get the global feature flags instance."""
    global _feature_flags
    if _feature_flags is None:
        _feature_flags = FeatureFlags()
    return _feature_flags


def get_tenant_from_request(request: Request) -> str:
    """
    Extract tenant ID from request.
    
    Checks in order:
    1. X-Tenant-ID header
    2. X-API-Key header (can be tenant-specific)
    3. tenant query parameter
    4. Default to "default"
    
    Args:
        request: FastAPI/Starlette request
    
    Returns:
        Tenant ID string
    """
    # Check header
    tenant_id = request.headers.get("X-Tenant-ID")
    if tenant_id:
        return tenant_id.strip()

    # Check API key (can be tenant-specific)
    api_key = request.headers.get("X-API-Key")
    if api_key:
        # If API key format is "tenant:key", extract tenant
        if ":" in api_key:
            tenant_id = api_key.split(":")[0]
            return tenant_id.strip()

    # Check query parameter
    tenant_id = request.query_params.get("tenant")
    if tenant_id:
        return tenant_id.strip()

    # Default tenant
    return "default"


def is_feature_enabled(feature: str, tenant: Optional[str] = None) -> bool:
    """
    Check if a feature is enabled for a tenant.
    
    Args:
        feature: Feature name
        tenant: Tenant ID (optional)
    
    Returns:
        True if enabled, False otherwise
    """
    flags = get_feature_flags()
    return flags.is_enabled(feature, tenant)


def require_feature(feature: str, tenant: Optional[str] = None) -> None:
    """
    Raise an exception if a feature is not enabled.
    
    Args:
        feature: Feature name
        tenant: Tenant ID (optional)
    
    Raises:
        ValueError: If feature is not enabled
    """
    if not is_feature_enabled(feature, tenant):
        raise ValueError(f"Feature '{feature}' is not enabled for tenant '{tenant or 'default'}'")

