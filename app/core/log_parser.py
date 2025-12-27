"""
Log File Parser

Parses various log file formats and extracts error entries for RCA analysis.
Supports: plain text logs, syslog, JSONL, CSV, and structured JSON.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path


def parse_plain_text_log(content: str, source: str = "log_file") -> List[Dict[str, Any]]:
    """
    Parse plain text log file and extract error entries.
    
    Looks for common error patterns:
    - ERROR, WARN, FATAL keywords
    - Exception traces
    - Error messages
    
    Args:
        content: Raw log file content
        source: Source identifier
    
    Returns:
        List of error objects
    """
    errors = []
    lines = content.split('\n')
    
    current_error = None
    error_buffer = []
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        
        # Detect error lines
        is_error = any(keyword in line.upper() for keyword in [
            'ERROR', 'ERR', 'FATAL', 'CRITICAL', 'EXCEPTION',
            'FAILED', 'FAILURE', 'TRACEBACK', 'STACK TRACE'
        ])
        
        # Detect stack trace continuation
        is_stack_trace = (
            line.startswith('  File ') or
            line.startswith('Traceback') or
            'at ' in line and ('line ' in line or '.py' in line)
        )
        
        if is_error or is_stack_trace:
            if current_error is None:
                # Start new error
                current_error = {
                    "message": line,
                    "stack_trace": "",
                    "timestamp": None,
                    "source": source,
                    "metadata": {"line_number": i + 1},
                }
                error_buffer = [line]
            else:
                # Continue error/stack trace
                error_buffer.append(line)
                if is_stack_trace:
                    current_error["stack_trace"] += line + "\n"
        else:
            # Try to extract timestamp
            if current_error and not current_error.get("timestamp"):
                timestamp = extract_timestamp(line)
                if timestamp:
                    current_error["timestamp"] = timestamp
            
            # End current error if we hit a non-error line and have content
            if current_error and error_buffer and not is_stack_trace:
                current_error["message"] = "\n".join(error_buffer[:5])  # First 5 lines
                if current_error["stack_trace"]:
                    current_error["stack_trace"] = current_error["stack_trace"].strip()
                errors.append(current_error)
                current_error = None
                error_buffer = []
    
    # Add final error if exists
    if current_error:
        current_error["message"] = "\n".join(error_buffer[:5])
        if current_error["stack_trace"]:
            current_error["stack_trace"] = current_error["stack_trace"].strip()
        errors.append(current_error)
    
    return errors


def parse_syslog(content: str, source: str = "syslog") -> List[Dict[str, Any]]:
    """
    Parse syslog format logs.
    
    Syslog format: timestamp hostname service[pid]: message
    
    Args:
        content: Raw syslog content
        source: Source identifier
    
    Returns:
        List of error objects
    """
    errors = []
    lines = content.split('\n')
    
    # Syslog pattern: Jan 15 10:30:00 hostname service[pid]: message
    syslog_pattern = re.compile(
        r'(\w+\s+\d+\s+\d+:\d+:\d+)\s+(\S+)\s+(\S+):\s*(.*)'
    )
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        match = syslog_pattern.match(line)
        if match:
            timestamp_str, hostname, service, message = match.groups()
            
            # Check if it's an error
            if any(keyword in message.upper() for keyword in [
                'ERROR', 'ERR', 'FATAL', 'CRITICAL', 'FAILED', 'FAILURE'
            ]):
                # Try to parse timestamp
                timestamp = parse_syslog_timestamp(timestamp_str)
                
                errors.append({
                    "message": message,
                    "stack_trace": "",
                    "timestamp": timestamp.isoformat() if timestamp else None,
                    "source": source,
                    "metadata": {
                        "hostname": hostname,
                        "service": service,
                        "log_format": "syslog",
                    },
                })
    
    return errors


def parse_jsonl_log(content: str, source: str = "jsonl_log") -> List[Dict[str, Any]]:
    """
    Parse JSONL (JSON Lines) log file.
    
    Each line is a JSON object.
    
    Args:
        content: Raw JSONL content
        source: Source identifier
    
    Returns:
        List of error objects
    """
    errors = []
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        try:
            entry = json.loads(line)
            
            # Check if it's an error entry
            level = str(entry.get("level", "")).upper()
            message = entry.get("message", "") or entry.get("msg", "") or str(entry)
            
            if any(keyword in level for keyword in ['ERROR', 'ERR', 'FATAL', 'CRITICAL']) or \
               any(keyword in str(message).upper() for keyword in ['ERROR', 'EXCEPTION', 'FAILED']):
                
                error_obj = {
                    "message": message,
                    "stack_trace": entry.get("stack_trace") or entry.get("traceback") or "",
                    "timestamp": entry.get("timestamp") or entry.get("time") or entry.get("@timestamp"),
                    "source": source,
                    "metadata": {
                        "level": level,
                        "log_format": "jsonl",
                        **{k: v for k, v in entry.items() if k not in ["message", "msg", "stack_trace", "traceback", "timestamp", "time", "@timestamp"]},
                    },
                }
                errors.append(error_obj)
        except json.JSONDecodeError:
            # Skip invalid JSON lines
            continue
    
    return errors


def parse_csv_log(content: str, source: str = "csv_log") -> List[Dict[str, Any]]:
    """
    Parse CSV log file (assumes timestamp, level, message columns).
    
    Args:
        content: Raw CSV content
        source: Source identifier
    
    Returns:
        List of error objects
    """
    errors = []
    lines = content.split('\n')
    
    if not lines:
        return errors
    
    # Try to detect header
    header = lines[0].split(',')
    timestamp_col = None
    level_col = None
    message_col = None
    
    for i, col in enumerate(header):
        col_lower = col.lower().strip()
        if 'time' in col_lower or 'date' in col_lower:
            timestamp_col = i
        if 'level' in col_lower or 'severity' in col_lower:
            level_col = i
        if 'message' in col_lower or 'msg' in col_lower or 'log' in col_lower:
            message_col = i
    
    # Default positions if not detected
    if timestamp_col is None:
        timestamp_col = 0
    if level_col is None:
        level_col = 1
    if message_col is None:
        message_col = 2
    
    for line in lines[1:]:  # Skip header
        parts = line.split(',')
        if len(parts) < max(timestamp_col, level_col, message_col) + 1:
            continue
        
        level = parts[level_col].strip().upper() if level_col < len(parts) else ""
        message = parts[message_col].strip() if message_col < len(parts) else ""
        timestamp = parts[timestamp_col].strip() if timestamp_col < len(parts) else None
        
        if any(keyword in level for keyword in ['ERROR', 'ERR', 'FATAL', 'CRITICAL']) or \
           any(keyword in message.upper() for keyword in ['ERROR', 'EXCEPTION', 'FAILED']):
            
            errors.append({
                "message": message,
                "stack_trace": "",
                "timestamp": timestamp,
                "source": source,
                "metadata": {
                    "level": level,
                    "log_format": "csv",
                },
            })
    
    return errors


def extract_timestamp(text: str) -> Optional[str]:
    """Extract ISO timestamp from text."""
    # ISO format: 2024-01-15T10:30:00Z or 2024-01-15T10:30:00+00:00
    iso_pattern = re.compile(
        r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?'
    )
    match = iso_pattern.search(text)
    if match:
        return match.group(0).replace(' ', 'T')
    
    # Common log formats
    # 2024-01-15 10:30:00
    date_pattern = re.compile(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}')
    match = date_pattern.search(text)
    if match:
        return match.group(0).replace(' ', 'T') + 'Z'
    
    return None


def parse_syslog_timestamp(timestamp_str: str) -> Optional[datetime]:
    """Parse syslog timestamp format: Jan 15 10:30:00"""
    try:
        # Current year assumption (could be improved)
        current_year = datetime.now().year
        dt = datetime.strptime(f"{current_year} {timestamp_str}", "%Y %b %d %H:%M:%S")
        return dt
    except Exception:
        return None


def parse_log_file(
    content: str,
    filename: str,
    file_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Auto-detect log file format and parse it.
    
    Args:
        content: Raw file content
        filename: Original filename
        file_type: Optional file type hint (jsonl, syslog, csv, text)
    
    Returns:
        List of error objects ready for ingestion
    """
    # Auto-detect file type
    if not file_type:
        filename_lower = filename.lower()
        if filename_lower.endswith('.jsonl') or filename_lower.endswith('.ndjson'):
            file_type = 'jsonl'
        elif filename_lower.endswith('.csv'):
            file_type = 'csv'
        elif 'syslog' in filename_lower:
            file_type = 'syslog'
        else:
            # Try to detect format from content
            first_line = content.split('\n')[0] if content else ""
            if first_line.startswith('{') and '\n' in content:
                # Multiple JSON objects (JSONL)
                file_type = 'jsonl'
            elif ',' in first_line and len(first_line.split(',')) >= 3:
                # CSV-like
                file_type = 'csv'
            elif re.match(r'\w+\s+\d+\s+\d+:\d+:\d+', first_line):
                # Syslog format
                file_type = 'syslog'
            else:
                file_type = 'text'
    
    # Parse based on type
    source = Path(filename).stem
    
    if file_type == 'jsonl':
        return parse_jsonl_log(content, source=source)
    elif file_type == 'csv':
        return parse_csv_log(content, source=source)
    elif file_type == 'syslog':
        return parse_syslog(content, source=source)
    else:
        # Plain text
        return parse_plain_text_log(content, source=source)

