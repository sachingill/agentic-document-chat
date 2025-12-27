"""
RCA (Root Cause Analysis) Tools

Specialized tools for analyzing application errors, finding patterns, and generating insights.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from langsmith import traceable

from app.agents.tools import retrieve_tool, keyword_search_tool, metadata_search_tool
from app.models.embeddings import VECTOR_DB
from app.models.llm_factory import main_llm


@traceable(name="error_pattern_search", run_type="tool")
def error_pattern_search(
    error_message: str,
    error_type: Optional[str] = None,
    metadata_filters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Search for similar error patterns in ingested logs.
    
    Args:
        error_message: The error message or stack trace snippet
        error_type: Optional error type/class name (e.g., "ValueError", "ConnectionError")
    
    Returns:
        Dict with similar errors, frequency, and pattern analysis
    """
    # Extract key error terms for better search
    # Try to extract error class/type from message
    error_class_match = re.search(r'(\w+Error|\w+Exception|Error|Exception)', error_message, re.IGNORECASE)
    extracted_error_type = error_class_match.group(1) if error_class_match else error_type
    
    # Build query with error type and key terms
    query = error_message[:500]  # Limit query length
    if extracted_error_type:
        # Prioritize error type in query
        query = f"{extracted_error_type} {query}"
    
    # Increase retrieval to get more context
    result = retrieve_tool(query, k=20)
    documents = result.get("documents", [])
    
    # Apply metadata filters if provided
    if metadata_filters:
        filtered_docs = []
        for doc in documents:
            meta = doc.get("metadata", {})
            match = True
            
            # Check each filter
            for key, value in metadata_filters.items():
                if key == "status" and isinstance(value, list):
                    # OR condition: status in [401, 403]
                    if meta.get("status") not in [str(v) for v in value]:
                        match = False
                        break
                elif key == "endpoint" and "pattern" in metadata_filters:
                    # Pattern match: endpoint contains pattern
                    endpoint = meta.get("endpoint", "")
                    pattern = metadata_filters.get("pattern", "")
                    if pattern not in endpoint:
                        match = False
                        break
                elif key == "latency_ms" and "operator" in metadata_filters:
                    # Comparison: latency_ms > 3000
                    operator = metadata_filters.get("operator", ">")
                    threshold = metadata_filters.get("value", 0)
                    try:
                        latency = float(meta.get("latency_ms", 0))
                        if operator == ">" and latency <= threshold:
                            match = False
                            break
                        elif operator == "<" and latency >= threshold:
                            match = False
                            break
                    except (ValueError, TypeError):
                        match = False
                        break
                elif meta.get(key) != value:
                    match = False
                    break
            
            if match:
                filtered_docs.append(doc)
        
        # Use filtered docs if we have matches, otherwise fall back to all docs
        if filtered_docs:
            documents = filtered_docs
    
    # Also try keyword search for exact error type match
    if extracted_error_type:
        keyword_result = keyword_search_tool(extracted_error_type)
        keyword_matches = keyword_result.get("matches", [])
        # Add keyword matches that aren't already in documents
        existing_texts = {doc.get("text", "")[:100] for doc in documents}
        for match in keyword_matches[:5]:
            if match[:100] not in existing_texts:
                documents.append({"text": match, "metadata": {"source": "keyword_search"}})
    
    # Extract error patterns with more detail
    patterns = []
    for doc in documents:
        text = doc.get("text", "")
        meta = doc.get("metadata", {})
        
        # Try to extract error type and message from text
        error_match = re.search(r'(?:(\w+Error|\w+Exception|Error|Exception))[:\s]+([^\n]+)', text, re.IGNORECASE)
        if error_match:
            error_snippet = f"{error_match.group(1)}: {error_match.group(2)[:150]}"
        else:
            # Fallback: extract first meaningful line
            lines = text.split('\n')
            error_snippet = next((line.strip() for line in lines if line.strip() and len(line.strip()) > 10), text[:150])
        
        patterns.append({
            "text": text[:500],  # Increased from 300 to 500 for more context
            "error_snippet": error_snippet,
            "metadata": meta,
            "timestamp": meta.get("timestamp") or meta.get("created_at"),
            "source": meta.get("filename") or meta.get("source") or "unknown",
        })
    
    return {
        "patterns": patterns,
        "count": len(patterns),
        "query": error_message[:200],
        "error_type_found": extracted_error_type,
    }


@traceable(name="stack_trace_analyzer", run_type="tool")
def stack_trace_analyzer(stack_trace: str) -> Dict[str, Any]:
    """
    Analyze stack trace to identify key components, file paths, and line numbers.
    
    Args:
        stack_trace: Full or partial stack trace
    
    Returns:
        Dict with analyzed components, file paths, line numbers, and root cause hints
    """
    llm = main_llm()
    
    prompt = f"""Analyze this stack trace and extract SPECIFIC technical details. Be precise and concrete.

Stack trace:
{stack_trace[:2000]}

Extract:
1. Main error type/class (exact class name)
2. Key file paths and line numbers (full paths, exact line numbers)
3. Component/module names involved (specific class/method names)
4. Likely root cause (SPECIFIC technical reason, e.g., "Null pointer at UserService.validate() line 45 because user object is None")
5. Suggested fix (SPECIFIC action, e.g., "Add null check before accessing user.email at line 45")

Respond in JSON format:
{{
    "error_type": "Exact error class name",
    "file_paths": ["Full path/to/file.py", "Full path/to/other.py"],
    "line_numbers": [45, 123],
    "components": ["UserService.validate", "DatabaseConnection.pool"],
    "root_cause_hint": "Specific technical root cause with file/line references",
    "suggested_fix": "Specific fix with code location and action"
}}
"""
    
    try:
        response = llm.invoke(prompt).content.strip()
        # Extract JSON from response
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            response = response.split("```")[1].split("```")[0].strip()
        
        analysis = json.loads(response)
    except Exception as e:
        analysis = {
            "error_type": "Unknown",
            "file_paths": [],
            "line_numbers": [],
            "components": [],
            "root_cause_hint": f"Failed to parse: {str(e)}",
            "suggested_fix": "Review stack trace manually",
        }
    
    return {
        "analysis": analysis,
        "stack_trace_length": len(stack_trace),
    }


@traceable(name="incident_correlator", run_type="tool")
def incident_correlator(
    error_message: str,
    timestamp: Optional[str] = None,
    time_window_hours: int = 24,
) -> Dict[str, Any]:
    """
    Find related incidents/errors that occurred around the same time or share similar patterns.
    
    Args:
        error_message: Error message to correlate
        timestamp: ISO timestamp of the error (optional)
        time_window_hours: Hours before/after to search
    
    Returns:
        Dict with correlated incidents and correlation scores
    """
    # Search for similar errors
    pattern_result = error_pattern_search(error_message)
    
    correlated = []
    if timestamp:
        try:
            error_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            window_start = error_time - timedelta(hours=time_window_hours)
            window_end = error_time + timedelta(hours=time_window_hours)
            
            for pattern in pattern_result.get("patterns", []):
                pattern_ts = pattern.get("timestamp")
                if pattern_ts:
                    try:
                        pt = datetime.fromisoformat(pattern_ts.replace("Z", "+00:00"))
                        if window_start <= pt <= window_end:
                            correlated.append(pattern)
                    except Exception:
                        pass
        except Exception:
            pass
    
    # If no time-based correlation, use top similar patterns
    if not correlated:
        correlated = pattern_result.get("patterns", [])[:5]
    
    return {
        "correlated_incidents": correlated,
        "count": len(correlated),
        "time_window_hours": time_window_hours,
    }


@traceable(name="trend_analyzer", run_type="tool")
def trend_analyzer(
    error_pattern: str,
    lookback_days: int = 7,
) -> Dict[str, Any]:
    """
    Analyze error frequency trends over time.
    
    Args:
        error_pattern: Error message pattern to analyze
        lookback_days: Number of days to look back
    
    Returns:
        Dict with trend data, frequency, and insights
    """
    # Search for all occurrences
    result = error_pattern_search(error_pattern)
    patterns = result.get("patterns", [])
    
    # Group by date (if timestamps available)
    daily_counts: Dict[str, int] = {}
    for pattern in patterns:
        ts = pattern.get("timestamp")
        if ts:
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                date_key = dt.date().isoformat()
                daily_counts[date_key] = daily_counts.get(date_key, 0) + 1
            except Exception:
                pass
    
    # Calculate trend
    total_count = len(patterns)
    avg_per_day = total_count / lookback_days if lookback_days > 0 else 0
    
    # Simple trend: increasing, decreasing, stable
    trend = "stable"
    if len(daily_counts) >= 2:
        dates = sorted(daily_counts.keys())
        recent = daily_counts.get(dates[-1], 0)
        older = daily_counts.get(dates[0], 0)
        if recent > older * 1.2:
            trend = "increasing"
        elif recent < older * 0.8:
            trend = "decreasing"
    
    return {
        "total_occurrences": total_count,
        "daily_counts": daily_counts,
        "average_per_day": round(avg_per_day, 2),
        "trend": trend,
        "lookback_days": lookback_days,
    }


@traceable(name="root_cause_analyzer", run_type="chain")
def root_cause_analyzer(
    error_message: str,
    stack_trace: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Comprehensive root cause analysis combining multiple tools.
    
    Args:
        error_message: The error message
        stack_trace: Optional full stack trace
        context: Optional additional context (timestamp, user_id, etc.)
    
    Returns:
        Dict with root cause analysis, insights, and recommendations
    """
    llm = main_llm()
    
    # Gather data from all tools
    pattern_result = error_pattern_search(error_message)
    stack_analysis = {}
    if stack_trace:
        stack_analysis = stack_trace_analyzer(stack_trace)
    
    timestamp = (context or {}).get("timestamp")
    correlator_result = incident_correlator(error_message, timestamp=timestamp)
    trend_result = trend_analyzer(error_message)
    
    # Extract actual error patterns for context
    similar_errors_text = ""
    if pattern_result.get("patterns"):
        similar_errors_text = "\n\nSimilar Errors Found:\n"
        for i, pattern in enumerate(pattern_result.get("patterns", [])[:5], 1):
            error_snippet = pattern.get("error_snippet", "")[:200]
            source = pattern.get("source", "unknown")
            timestamp = pattern.get("timestamp", "")
            similar_errors_text += f"{i}. [{source}] {timestamp}: {error_snippet}\n"
    
    # Extract correlated incidents details
    correlated_text = ""
    if correlator_result.get("correlated_incidents"):
        correlated_text = "\n\nCorrelated Incidents (same time window):\n"
        for i, incident in enumerate(correlator_result.get("correlated_incidents", [])[:3], 1):
            error_snippet = incident.get("error_snippet", "")[:150]
            source = incident.get("source", "unknown")
            correlated_text += f"{i}. [{source}]: {error_snippet}\n"
    
    # Build comprehensive analysis prompt with actual data
    analysis_prompt = f"""You are an expert Root Cause Analysis engineer. Analyze this application error and provide a SPECIFIC, ACTIONABLE RCA report.

CURRENT ERROR:
{error_message}

STACK TRACE ANALYSIS:
{json.dumps(stack_analysis.get('analysis', {}), indent=2) if stack_analysis else 'No stack trace provided'}

HISTORICAL CONTEXT:
- Similar errors found: {pattern_result.get('count', 0)} occurrences
- Trend: {trend_result.get('trend', 'unknown')} ({trend_result.get('total_occurrences', 0)} total occurrences)
- Average per day: {trend_result.get('average_per_day', 0)}
{similar_errors_text}
{correlated_text}

INSTRUCTIONS:
1. Root Cause: Be SPECIFIC. Identify the exact technical cause (e.g., "Null pointer exception in UserService.validate() due to missing null check" NOT "A validation error occurred")
2. Contributing Factors: List SPECIFIC technical/system factors (e.g., "Missing input validation", "Database connection pool exhausted", "Race condition in cache invalidation")
3. Severity: Assess based on impact (critical=system down, high=major feature broken, medium=partial degradation, low=minor issue)
4. Impact: Be SPECIFIC about what breaks and for whom (e.g., "All user login attempts fail, affecting 100% of users" NOT "Users are affected")
5. Recommended Fixes: Provide ACTIONABLE, SPECIFIC steps with code/file references if available (e.g., "Add null check in UserService.validate() line 45" NOT "Fix the validation")
6. Prevention: SPECIFIC measures (e.g., "Add unit tests for null input scenarios", "Implement circuit breaker for database connections")
7. Insights: SPECIFIC observations from the data (e.g., "Error occurs 3x more frequently during peak hours", "All occurrences involve users with expired sessions")

Provide a comprehensive RCA report in JSON format:
{{
    "root_cause": "Specific technical root cause with file/component references if available",
    "contributing_factors": ["specific factor 1", "specific factor 2"],
    "severity": "low|medium|high|critical",
    "impact": "Specific description of what breaks and who is affected",
    "recommended_fixes": [
        {{"action": "Specific actionable fix with code/file references", "priority": "high|medium|low", "location": "file/component if known"}}
    ],
    "prevention_measures": ["Specific prevention measure 1", "Specific prevention measure 2"],
    "insights": ["Specific insight from data analysis 1", "Specific insight from data analysis 2"]
}}
"""
    
    try:
        response = llm.invoke(analysis_prompt).content.strip()
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            response = response.split("```")[1].split("```")[0].strip()
        
        rca_report = json.loads(response)
    except Exception as e:
        rca_report = {
            "root_cause": f"Analysis failed: {str(e)}",
            "contributing_factors": [],
            "severity": "unknown",
            "impact": "Unable to assess",
            "recommended_fixes": [],
            "prevention_measures": [],
            "insights": [],
        }
    
    return {
        "rca_report": rca_report,
        "pattern_analysis": pattern_result,
        "stack_analysis": stack_analysis,
        "correlation": correlator_result,
        "trends": trend_result,
    }

