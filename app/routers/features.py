"""
Feature Flags Router

Exposes feature flag information to clients.
"""

from __future__ import annotations

from typing import Dict, Any

from fastapi import APIRouter, Request

from app.core.feature_flags import get_tenant_from_request, get_feature_flags

router = APIRouter(tags=["features"])


@router.get("/features")
async def get_features(request: Request) -> Dict[str, Any]:
    """
    Get all feature flags for the current tenant.
    
    Returns which features are enabled/disabled for the tenant making the request.
    """
    tenant = get_tenant_from_request(request)
    flags = get_feature_flags()
    features = flags.get_tenant_features(tenant)
    
    return {
        "tenant": tenant,
        "features": features,
    }


@router.get("/features/{feature_name}")
async def check_feature(feature_name: str, request: Request) -> Dict[str, Any]:
    """
    Check if a specific feature is enabled for the current tenant.
    
    Args:
        feature_name: Name of the feature to check
    
    Returns:
        Dict with feature name and enabled status
    """
    tenant = get_tenant_from_request(request)
    flags = get_feature_flags()
    enabled = flags.is_enabled(feature_name, tenant)
    
    return {
        "tenant": tenant,
        "feature": feature_name,
        "enabled": enabled,
    }

