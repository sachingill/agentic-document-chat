"""
RCA (Root Cause Analysis) Router

FastAPI endpoints for error analysis and RCA chatbot.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from pydantic import BaseModel, Field

from app.agents.rca_agent import run_rca_agent
from app.agents.guardrails import check_input_safety, check_output_safety
from app.models.embeddings import ingest_documents
from app.core.feature_flags import get_tenant_from_request, is_feature_enabled
from app.core.log_parser import parse_log_file
from app.core.known_issues import (
    get_all_known_issues,
    get_known_issue,
    build_query_for_issue,
    get_metadata_filters_for_issue,
)

router = APIRouter(tags=["rca"])


class ErrorIngestRequest(BaseModel):
    """Request model for ingesting error logs"""
    errors: List[Dict[str, Any]] = Field(
        ...,
        description="List of error objects with 'message', 'stack_trace' (optional), 'timestamp' (optional), etc."
    )


class RCAChatRequest(BaseModel):
    """Request model for RCA chat"""
    error_message: str = Field(..., min_length=1, description="The error message to analyze")
    stack_trace: Optional[str] = Field(None, description="Optional full stack trace")
    context: Optional[Dict[str, Any]] = Field(None, description="Optional context (timestamp, user_id, environment, etc.)")
    include_trends: bool = Field(True, description="Whether to include trend analysis")


class RCAChatResponse(BaseModel):
    """Response model for RCA chat"""
    summary: str
    rca_report: Dict[str, Any]
    pattern_analysis: Dict[str, Any]
    stack_analysis: Dict[str, Any]
    correlation: Dict[str, Any]
    trends: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
    insights: List[str]
    citations: List[Dict[str, Any]]
    guardrail: Optional[Dict[str, Any]] = None


@router.post("/rca/ingest/errors")
async def ingest_errors(payload: ErrorIngestRequest, request: Request) -> Dict[str, Any]:
    """
    Ingest error logs into the vector DB for RCA analysis.
    
    Each error object should have:
    - message: Error message (required)
    - stack_trace: Full stack trace (optional)
    - timestamp: ISO timestamp (optional)
    - source: Source file/service (optional)
    - metadata: Additional metadata (optional)
    
    Requires 'rca_ingest' feature flag to be enabled for the tenant.
    """
    # Check feature flag
    tenant = get_tenant_from_request(request)
    if not is_feature_enabled("rca_ingest", tenant):
        raise HTTPException(
            status_code=403,
            detail=f"RCA ingest feature is not enabled for tenant '{tenant}'. Contact support to enable this feature.",
        )
    texts: List[str] = []
    metadatas: List[Dict[str, Any]] = []
    
    for error in payload.errors:
        error_msg = error.get("message", "")
        stack_trace = error.get("stack_trace", "")
        timestamp = error.get("timestamp")
        source = error.get("source", "unknown")
        metadata = error.get("metadata", {})
        
        # Combine message + stack trace for ingestion
        full_text = error_msg
        if stack_trace:
            full_text = f"{error_msg}\n\nStack Trace:\n{stack_trace}"
        
        texts.append(full_text)
        
        # Build metadata
        meta = {
            "type": "error_log",
            "source": source,
            "timestamp": timestamp or datetime.now().isoformat(),
            **metadata,
        }
        metadatas.append(meta)
    
    if not texts:
        raise HTTPException(status_code=400, detail="No errors provided")
    
    ingest_documents(texts, metadata=metadatas)
    
    return {
        "status": "success",
        "items_ingested": len(texts),
        "message": f"Successfully ingested {len(texts)} error logs",
    }


@router.post("/rca/ingest/logfile")
async def ingest_log_file(
    file: UploadFile = File(...),
    file_type: Optional[str] = None,
    request: Request = None,
) -> Dict[str, Any]:
    """
    Upload and parse a log file, then ingest extracted errors.
    
    Supports multiple log formats:
    - Plain text logs (.log, .txt)
    - Syslog format (.log)
    - JSONL/NDJSON (.jsonl, .ndjson)
    - CSV logs (.csv)
    - JSON error logs (.json)
    
    Args:
        file: Uploaded log file
        file_type: Optional file type hint (jsonl, syslog, csv, text, json)
        request: FastAPI request object
    
    Returns:
        Status and count of ingested errors
    """
    # Check feature flag
    tenant = get_tenant_from_request(request) if request else "default"
    if not is_feature_enabled("rca_ingest", tenant):
        raise HTTPException(
            status_code=403,
            detail=f"RCA ingest feature is not enabled for tenant '{tenant}'. Contact support to enable this feature.",
        )
    
    # Read file content
    try:
        content_bytes = await file.read()
        content_str = content_bytes.decode("utf-8", errors="ignore")
        filename = file.filename or "unknown.log"
        file_size_mb = round(len(content_bytes) / (1024 * 1024), 2)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")
    
    # Parse log file
    try:
        errors = parse_log_file(content_str, filename=filename, file_type=file_type)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to parse log file: {str(e)}",
        )
    
    if not errors:
        return {
            "status": "success",
            "items_ingested": 0,
            "message": "No errors found in log file",
            "warnings": ["No error entries detected. Make sure the log file contains error messages."],
            "file_info": {
                "filename": filename,
                "format": file_type or "auto-detected",
                "file_size_mb": file_size_mb,
            },
        }
    
    # Prepare for ingestion and collect statistics
    texts: List[str] = []
    metadatas: List[Dict[str, Any]] = []
    
    # Statistics for summary
    error_types: Dict[str, int] = {}
    error_levels: Dict[str, int] = {}
    sample_errors: List[Dict[str, Any]] = []
    has_stack_traces = 0
    timestamp_range = {"earliest": None, "latest": None}
    
    for error in errors:
        error_msg = error.get("message", "")
        stack_trace = error.get("stack_trace", "")
        timestamp = error.get("timestamp")
        source = error.get("source", filename)
        metadata = error.get("metadata", {})
        
        # Extract error type from message (first word before colon or space)
        error_type = "Unknown"
        if error_msg:
            parts = error_msg.split(":", 1)
            if len(parts) > 0:
                error_type = parts[0].strip()
                if len(error_type) > 50:
                    error_type = error_type[:50] + "..."
        
        # Count error types
        error_types[error_type] = error_types.get(error_type, 0) + 1
        
        # Count error levels
        level = metadata.get("level", "").upper() or "ERROR"
        error_levels[level] = error_levels.get(level, 0) + 1
        
        # Track stack traces
        if stack_trace:
            has_stack_traces += 1
        
        # Track timestamps
        if timestamp:
            if not timestamp_range["earliest"] or timestamp < timestamp_range["earliest"]:
                timestamp_range["earliest"] = timestamp
            if not timestamp_range["latest"] or timestamp > timestamp_range["latest"]:
                timestamp_range["latest"] = timestamp
        
        # Collect sample errors (first 3)
        if len(sample_errors) < 3:
            sample_errors.append({
                "message": error_msg[:200] + "..." if len(error_msg) > 200 else error_msg,
                "type": error_type,
                "timestamp": timestamp,
            })
        
        # Combine message + stack trace for ingestion
        full_text = error_msg
        if stack_trace:
            full_text = f"{error_msg}\n\nStack Trace:\n{stack_trace}"
        
        texts.append(full_text)
        
        # Build metadata
        meta = {
            "type": "error_log",
            "source": source,
            "filename": filename,
            "timestamp": timestamp or datetime.now().isoformat(),
            **metadata,
        }
        metadatas.append(meta)
    
    # Ingest into vector DB
    try:
        ingest_documents(texts, metadata=metadatas)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to ingest errors: {str(e)}",
        )
    
    # Prepare summary statistics
    top_error_types = sorted(error_types.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return {
        "status": "success",
        "items_ingested": len(texts),
        "message": f"Successfully parsed and ingested {len(texts)} errors from log file",
        "file_info": {
            "filename": filename,
            "format": file_type or "auto-detected",
            "errors_found": len(errors),
            "file_size_mb": file_size_mb,
        },
        "summary": {
            "total_errors": len(errors),
            "total_documents_ingested": len(texts),
            "error_types": dict(top_error_types),
            "error_levels": error_levels,
            "has_stack_traces": has_stack_traces,
            "timestamp_range": timestamp_range,
            "sample_errors": sample_errors,
        },
    }


@router.get("/rca/check-file/{filename:path}")
async def check_file_ingestion(filename: str, request: Request) -> Dict[str, Any]:
    """
    Check if a specific log file has been ingested into the vector database.
    
    Args:
        filename: Name of the file to check (can include path)
        request: FastAPI request object
    
    Returns:
        Status and count of documents found for this filename
    """
    try:
        from app.models.embeddings import VECTOR_DB
        
        # Get collection
        collection = VECTOR_DB._collection
        
        # Try to get documents with matching filename in metadata
        try:
            # Use ChromaDB's get with where clause
            results = collection.get(
                where={"filename": filename},
                limit=10000
            )
            
            if results and results.get("ids"):
                count = len(results["ids"])
                sample_meta = results["metadatas"][0] if results.get("metadatas") else {}
                
                return {
                    "status": "found",
                    "filename": filename,
                    "document_count": count,
                    "sample_metadata": sample_meta,
                    "message": f"Found {count} documents ingested from '{filename}'",
                }
            else:
                # Fallback: search all documents
                all_results = collection.get(limit=10000)
                matching = []
                
                if all_results and all_results.get("metadatas"):
                    for i, metadata in enumerate(all_results["metadatas"]):
                        if metadata and metadata.get("filename") == filename:
                            matching.append(i)
                
                if matching:
                    count = len(matching)
                    sample_meta = all_results["metadatas"][matching[0]] if all_results.get("metadatas") else {}
                    
                    return {
                        "status": "found",
                        "filename": filename,
                        "document_count": count,
                        "sample_metadata": sample_meta,
                        "message": f"Found {count} documents ingested from '{filename}'",
                    }
                else:
                    return {
                        "status": "not_found",
                        "filename": filename,
                        "document_count": 0,
                        "message": f"No documents found for filename '{filename}'",
                        "total_documents_checked": len(all_results.get("metadatas", [])) if all_results else 0,
                    }
                    
        except Exception as e:
            # If where clause doesn't work, try manual search
            all_results = collection.get(limit=10000)
            matching = []
            
            if all_results and all_results.get("metadatas"):
                for i, metadata in enumerate(all_results["metadatas"]):
                    if metadata and metadata.get("filename") == filename:
                        matching.append(i)
            
            if matching:
                count = len(matching)
                sample_meta = all_results["metadatas"][matching[0]] if all_results.get("metadatas") else {}
                
                return {
                    "status": "found",
                    "filename": filename,
                    "document_count": count,
                    "sample_metadata": sample_meta,
                    "message": f"Found {count} documents ingested from '{filename}'",
                }
            else:
                return {
                    "status": "not_found",
                    "filename": filename,
                    "document_count": 0,
                    "message": f"No documents found for filename '{filename}'",
                    "total_documents_checked": len(all_results.get("metadatas", [])) if all_results else 0,
                    "error": str(e),
                }
                
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error checking file ingestion: {str(e)}",
        )


@router.post("/rca/chat", response_model=RCAChatResponse)
async def rca_chat(payload: RCAChatRequest, request: Request) -> RCAChatResponse:
    """
    Perform Root Cause Analysis on an error message.
    
    Returns comprehensive RCA report with root cause, recommendations, insights, and citations.
    
    Requires 'rca_chat' feature flag to be enabled for the tenant.
    """
    # Check feature flag
    tenant = get_tenant_from_request(request)
    if not is_feature_enabled("rca_chat", tenant):
        raise HTTPException(
            status_code=403,
            detail=f"RCA chat feature is not enabled for tenant '{tenant}'. Contact support to enable this feature.",
        )
    # Input guardrail
    gr_in = check_input_safety(payload.error_message)
    if not gr_in.allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Input blocked by safety policies: {gr_in.reason}",
        )
    
    # Run RCA agent
    try:
        result = await run_rca_agent(
            error_message=payload.error_message,
            stack_trace=payload.stack_trace,
            context=payload.context,
            include_trends=payload.include_trends,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"RCA analysis failed: {str(e)}",
        )
    
    # Output guardrail
    summary = result.get("summary", "")
    gr_out = check_output_safety(summary)
    
    guardrail_info = None
    if not gr_out.allowed:
        guardrail_info = {
            "stage": "output",
            "blocked": True,
            "reason": gr_out.reason,
        }
        # Sanitize summary if needed
        summary = gr_out.sanitized_text or summary
    
    return RCAChatResponse(
        summary=summary,
        rca_report=result.get("rca_report", {}),
        pattern_analysis=result.get("pattern_analysis", {}),
        stack_analysis=result.get("stack_analysis", {}),
        correlation=result.get("correlation", {}),
        trends=result.get("trends", {}),
        recommendations=result.get("recommendations", []),
        insights=result.get("insights", []),
        citations=result.get("citations", []),
        guardrail=guardrail_info,
    )


@router.get("/rca/features")
async def get_rca_features(request: Request) -> Dict[str, Any]:
    """
    Get available RCA features for the current tenant.
    
    Returns which RCA features are enabled/disabled.
    """
    tenant = get_tenant_from_request(request)
    from app.core.feature_flags import get_feature_flags
    
    flags = get_feature_flags()
    features = flags.get_tenant_features(tenant)
    
    return {
        "tenant": tenant,
        "features": {
            "rca_chat": features.get("rca_chat", False),
            "rca_ingest": features.get("rca_ingest", False),
        },
        "all_features": features,
    }


@router.get("/rca/known-issues")
async def get_known_issues() -> Dict[str, Any]:
    """
    Get all known issue templates for one-click RCA.
    
    Returns list of predefined issue templates.
    """
    issues = get_all_known_issues()
    return {
        "known_issues": issues,
        "count": len(issues),
    }


@router.post("/rca/quick/{issue_id}")
async def quick_rca(issue_id: str, request: Request) -> RCAChatResponse:
    """
    Perform one-click RCA for a known issue template.
    
    Args:
        issue_id: ID of the known issue template
    
    Returns:
        RCA analysis response
    """
    # Check feature flag
    tenant = get_tenant_from_request(request)
    if not is_feature_enabled("rca_chat", tenant):
        raise HTTPException(
            status_code=403,
            detail=f"RCA chat feature is not enabled for tenant '{tenant}'.",
        )
    
    # Get known issue template
    issue = get_known_issue(issue_id)
    if not issue:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown issue template: {issue_id}",
        )
    
    # Build query and metadata filters from template
    query = build_query_for_issue(issue)
    metadata_filters = get_metadata_filters_for_issue(issue)
    
    # Create a descriptive error message for analysis
    error_message = f"{issue['name']}: {issue['description']}\n\nSearch pattern: {query}"
    if metadata_filters:
        error_message += f"\nMetadata filters: {metadata_filters}"
    
    # Run RCA analysis with metadata filters
    try:
        # Import here to avoid circular import
        from app.agents.rca_tools import error_pattern_search
        
        # Override error_pattern_search to use metadata filters
        # We'll pass filters through context and let the agent use them
        result = await run_rca_agent(
            error_message=error_message,
            stack_trace=None,
            context={
                "known_issue_id": issue_id,
                "query": query,
                "metadata_filters": metadata_filters,
            },
            include_trends=True,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"RCA analysis failed: {str(e)}",
        )
    
    # Output guardrail
    summary = result.get("summary", "")
    from app.agents.guardrails import check_output_safety
    gr_out = check_output_safety(summary)
    
    guardrail_info = None
    if not gr_out.allowed:
        guardrail_info = {
            "stage": "output",
            "blocked": True,
            "reason": gr_out.reason,
        }
        summary = gr_out.sanitized_text or summary
    
    return RCAChatResponse(
        summary=summary,
        rca_report=result.get("rca_report", {}),
        pattern_analysis=result.get("pattern_analysis", {}),
        stack_analysis=result.get("stack_analysis", {}),
        correlation=result.get("correlation", {}),
        trends=result.get("trends", {}),
        recommendations=result.get("recommendations", []),
        insights=result.get("insights", []),
        citations=result.get("citations", []),
        guardrail=guardrail_info,
    )

