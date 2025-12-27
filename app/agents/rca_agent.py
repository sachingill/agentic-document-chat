"""
RCA (Root Cause Analysis) Agent

Specialized agent workflow for analyzing application errors and generating insights.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from langsmith import traceable

from app.agents.rca_tools import (
    error_pattern_search,
    incident_correlator,
    root_cause_analyzer,
    stack_trace_analyzer,
    trend_analyzer,
)
from app.models.llm_factory import main_llm


@traceable(name="rca_agent", run_type="chain")
async def run_rca_agent(
    error_message: str,
    stack_trace: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    include_trends: bool = True,
) -> Dict[str, Any]:
    """
    Run comprehensive RCA analysis on an error.
    
    Args:
        error_message: The error message
        stack_trace: Optional full stack trace
        context: Optional context (timestamp, user_id, environment, etc.)
        include_trends: Whether to include trend analysis (slower)
    
    Returns:
        Dict with RCA report, insights, citations, and recommendations
    """
    context = context or {}
    
    # Step 1: Pattern search (with metadata filters if provided)
    metadata_filters = context.get("metadata_filters")
    pattern_result = error_pattern_search(
        error_message,
        metadata_filters=metadata_filters,
    )
    
    # Step 2: Stack trace analysis (if provided)
    stack_analysis = {}
    if stack_trace:
        stack_analysis = stack_trace_analyzer(stack_trace)
    
    # Step 3: Correlation analysis
    timestamp = context.get("timestamp")
    correlation = incident_correlator(error_message, timestamp=timestamp)
    
    # Step 4: Trend analysis (optional, can be slow)
    trends = {}
    if include_trends:
        trends = trend_analyzer(error_message)
    
    # Step 5: Comprehensive RCA
    rca_result = root_cause_analyzer(
        error_message=error_message,
        stack_trace=stack_trace,
        context=context,
    )
    
    # Step 6: Generate natural language summary with specific details
    llm = main_llm()
    
    # Extract specific details for summary
    rca_report = rca_result.get('rca_report', {})
    root_cause = rca_report.get('root_cause', 'Unable to determine')
    severity = rca_report.get('severity', 'unknown')
    impact = rca_report.get('impact', 'Unknown impact')
    top_fixes = rca_report.get('recommended_fixes', [])[:3]
    insights = rca_report.get('insights', [])[:2]
    
    # Build context from actual findings
    similar_count = pattern_result.get('count', 0)
    trend_info = ""
    if trends.get('total_occurrences', 0) > 0:
        trend_info = f" This error has occurred {trends.get('total_occurrences', 0)} times, showing a {trends.get('trend', 'stable')} trend."
    
    # Include stack trace details if available
    stack_details = ""
    if stack_analysis.get('analysis'):
        stack_info = stack_analysis.get('analysis', {})
        if stack_info.get('file_paths'):
            stack_details = f" The error originates from: {', '.join(stack_info.get('file_paths', [])[:2])}."
    
    summary_prompt = f"""Generate a SPECIFIC, ACTIONABLE summary of this Root Cause Analysis. Avoid vague language - use concrete details.

ROOT CAUSE:
{root_cause}

SEVERITY: {severity.upper()}
IMPACT: {impact}

HISTORICAL DATA:
- Found {similar_count} similar error occurrences{trend_info}
- Correlated incidents: {correlation.get('count', 0)}{stack_details}

TOP RECOMMENDED FIXES:
{chr(10).join([f"{i+1}. [{fix.get('priority', 'medium').upper()}] {fix.get('action', '')}" for i, fix in enumerate(top_fixes)])}

KEY INSIGHTS:
{chr(10).join([f"- {insight}" for insight in insights]) if insights else "- No specific insights available"}

Write a clear, professional summary (3-4 paragraphs) that:
1. **First paragraph**: State the SPECIFIC root cause with technical details (include file/component names if available)
2. **Second paragraph**: Explain the SPECIFIC impact - what breaks, who is affected, severity level
3. **Third paragraph**: List the top 3 recommended fixes with priorities and specific actions
4. **Fourth paragraph**: Highlight key insights from the data analysis (trends, patterns, correlations)

Use concrete language. Avoid phrases like "may be", "could be", "possibly". Use "is", "occurs", "affects" with specific details.

Summary:"""
    
    try:
        summary = llm.invoke(summary_prompt).content.strip()
    except Exception:
        summary = f"RCA analysis completed. Root cause: {rca_result.get('rca_report', {}).get('root_cause', 'Unable to determine')}"
    
    # Build citations from retrieved patterns
    citations = []
    for pattern in pattern_result.get("patterns", [])[:5]:
        citations.append({
            "text": pattern.get("text", "")[:500],
            "metadata": {
                **pattern.get("metadata", {}),
                "error_snippet": pattern.get("error_snippet", ""),
            },
        })
    
    return {
        "summary": summary,
        "rca_report": rca_result.get("rca_report", {}),
        "pattern_analysis": {
            "similar_errors_count": pattern_result.get("count", 0),
            "patterns": pattern_result.get("patterns", [])[:3],
        },
        "stack_analysis": stack_analysis.get("analysis", {}),
        "correlation": {
            "correlated_incidents_count": correlation.get("count", 0),
            "incidents": correlation.get("correlated_incidents", [])[:3],
        },
        "trends": trends,
        "recommendations": rca_result.get("rca_report", {}).get("recommended_fixes", []),
        "insights": rca_result.get("rca_report", {}).get("insights", []),
        "citations": citations,
    }

