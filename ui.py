"""
RAG Chat UI - Streamlit Application

A simple, elegant, and intuitive UI for both Structured and Agentic RAG workflows.
"""

import streamlit as st
import requests
import json
import os
import io
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid

from pypdf import PdfReader

# ============================================================================
# CONFIGURATION
# ============================================================================
# Use environment variables for production, fallback to localhost for development

STRUCTURED_API_URL = os.getenv("STRUCTURED_API_URL", "http://localhost:8000")
# Default agentic URL to the same server since we now support a unified single API.
AGENTIC_API_URL = os.getenv("AGENTIC_API_URL", STRUCTURED_API_URL)

# Feature flags / tenant configuration
TENANT_ID = os.getenv("TENANT_ID", "default")  # Can be overridden in UI

WORKFLOW_STRUCTURED = "Structured RAG"
WORKFLOW_AGENTIC = "Agentic RAG"

NAV_CHAT = "Chat"
NAV_KB = "Knowledge Base"
NAV_RCA = "RCA Chat"

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="RAG Chat Interface",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM CSS FOR ELEGANT DESIGN
# ============================================================================

st.markdown("""
<style>
    /* Main container */
    .main {
        padding: 2rem;
    }
    
    /* Chat messages */
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .assistant-message {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 15px;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 500;
        margin: 0.25rem;
    }
    
    .status-success {
        background: #d4edda;
        color: #155724;
    }
    
    .status-warning {
        background: #fff3cd;
        color: #856404;
    }
    
    .status-danger {
        background: #f8d7da;
        color: #721c24;
    }
    
    /* Workflow selector */
    .workflow-card {
        padding: 1.5rem;
        border-radius: 10px;
        border: 2px solid #e0e0e0;
        margin: 1rem 0;
        transition: all 0.3s;
    }
    
    .workflow-card.active {
        border-color: #667eea;
        background: #f0f4ff;
    }
    
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    /* Keep header visible so the sidebar collapse/expand control continues to work */
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "kb_messages" not in st.session_state:
    st.session_state.kb_messages = []

if "rca_messages" not in st.session_state:
    st.session_state.rca_messages = []

if "page" not in st.session_state:
    st.session_state.page = NAV_CHAT

if "workflow" not in st.session_state:
    st.session_state.workflow = WORKFLOW_STRUCTURED  # Default

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "kb_session_id" not in st.session_state:
    st.session_state.kb_session_id = str(uuid.uuid4())

if "rca_session_id" not in st.session_state:
    st.session_state.rca_session_id = str(uuid.uuid4())

if "rca_call_to_ops_logs" not in st.session_state:
    st.session_state.rca_call_to_ops_logs = []

if "tenant_id" not in st.session_state:
    st.session_state.tenant_id = TENANT_ID

if "feature_flags" not in st.session_state:
    st.session_state.feature_flags = {}

if "inference_mode" not in st.session_state:
    st.session_state.inference_mode = "balanced"

if "api_status" not in st.session_state:
    st.session_state.api_status = {
        "structured": None,
        "agentic": None,
        "multiagent": None,
    }

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def check_api_status(api_url: str, status_key: str) -> bool:
    """Check if API is running"""
    try:
        response = requests.get(f"{api_url}/", timeout=2)
        if response.status_code == 200:
            st.session_state.api_status[status_key] = True
            return True
        else:
            # Non-200 status code - API is not healthy
            st.session_state.api_status[status_key] = False
            return False
    except Exception:
        # Exception occurred - API is not reachable
        st.session_state.api_status[status_key] = False
        return False

def _is_multiagent_workflow(workflow: str) -> bool:
    return workflow.startswith("Multi-agent")


def send_feedback(
    *,
    question: str,
    answer: str,
    thumbs_up: Optional[bool],
    comment: Optional[str] = None,
    expected_answer: Optional[str] = None,
) -> Dict:
    """
    Send user feedback to backend so it can be logged to LangSmith.
    Uses the Structured server (8000) because that's where /agent/feedback is mounted.
    """
    payload = {
        "session_id": st.session_state.session_id,
        "question": question,
        "answer": answer,
        "thumbs_up": thumbs_up,
        "comment": comment,
        "expected_answer": expected_answer,
    }
    try:
        resp = requests.post(
            f"{STRUCTURED_API_URL}/agent/feedback",
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        return {"status": "error", "error": str(e)}


def send_chat_message(
    question: str,
    workflow: str,
    *,
    multiagent_pattern: Optional[str] = None,
    auto_select_pattern: bool = True,
    max_relative_cost: Optional[float] = None,
    max_relative_latency: Optional[float] = None,
) -> Dict:
    """Send chat message to appropriate API"""
    # Default to Structured RAG
    api_url = STRUCTURED_API_URL
    endpoint = "/agent/chat"
    payload = {
        "question": question,
        "session_id": st.session_state.session_id,
        "inference_mode": st.session_state.get("inference_mode", "balanced"),
    }

    if workflow == WORKFLOW_AGENTIC:
        api_url = AGENTIC_API_URL
        endpoint = "/agentic/chat"
    elif _is_multiagent_workflow(workflow):
        # Multi-agent runs on the main API server (same as Structured)
        api_url = STRUCTURED_API_URL
        endpoint = "/multiagent/chat"
        payload = {
            "question": question,
            "session_id": st.session_state.session_id,
            "auto_select_pattern": auto_select_pattern,
            "inference_mode": st.session_state.get("inference_mode", "balanced"),
        }
        if not auto_select_pattern and multiagent_pattern:
            payload["pattern"] = multiagent_pattern
        if max_relative_cost is not None:
            payload["max_relative_cost"] = max_relative_cost
        if max_relative_latency is not None:
            payload["max_relative_latency"] = max_relative_latency
    
    try:
        response = requests.post(
            f"{api_url}{endpoint}",
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "error": f"API Error: {str(e)}",
            "answer": "Unable to connect to the API. Please ensure the server is running."
        }


def send_structured_chat(
    question: str,
    *,
    session_id: str,
    inference_mode: str,
) -> Dict:
    """Call the Structured endpoint directly (used by the Knowledge Base Agent)."""
    try:
        resp = requests.post(
            f"{STRUCTURED_API_URL}/agent/chat",
            json={
                "question": question,
                "session_id": session_id,
                "inference_mode": inference_mode,
            },
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        return {
            "error": f"API Error: {str(e)}",
            "answer": "Unable to connect to the API. Please ensure the server is running.",
            "citations": [],
        }


def ingest_texts(
    *,
    texts: List[str],
    metadatas: Optional[List[Dict]] = None,
    api_url: str = STRUCTURED_API_URL,
) -> Dict:
    """Ingest texts into the backend vector DB via /agent/ingest/json."""
    payload = {"texts": texts, "metadatas": metadatas}
    try:
        resp = requests.post(f"{api_url}/agent/ingest/json", json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        return {"status": "error", "error": str(e)}


def get_kb_status(api_url: str = STRUCTURED_API_URL) -> Dict:
    """Fetch vector DB status from the backend."""
    try:
        resp = requests.get(f"{api_url}/agent/debug/status", timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        return {"status": "error", "error": str(e)}




def send_rca_chat(
    error_message: str,
    stack_trace: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    include_trends: bool = True,
    api_url: str = STRUCTURED_API_URL,
    tenant_id: Optional[str] = None,
) -> Dict:
    """Send RCA chat request to analyze an error."""
    payload = {
        "error_message": error_message,
        "stack_trace": stack_trace,
        "context": context,
        "include_trends": include_trends,
    }
    headers = {}
    if tenant_id:
        headers["X-Tenant-ID"] = tenant_id
    try:
        resp = requests.post(f"{api_url}/rca/chat", json=payload, headers=headers, timeout=120)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        return {
            "error": f"API Error: {str(e)}",
            "summary": "Unable to connect to the RCA API. Please ensure the server is running.",
            "rca_report": {},
            "citations": [],
        }


def ingest_errors(errors: List[Dict[str, Any]], api_url: str = STRUCTURED_API_URL, tenant_id: Optional[str] = None) -> Dict:
    """Ingest error logs into the backend for RCA analysis."""
    payload = {"errors": errors}
    headers = {}
    if tenant_id:
        headers["X-Tenant-ID"] = tenant_id
    try:
        resp = requests.post(f"{api_url}/rca/ingest/errors", json=payload, headers=headers, timeout=120)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        return {"status": "error", "error": str(e)}


def ingest_log_file(file_content: bytes, filename: str, file_type: Optional[str] = None, api_url: str = STRUCTURED_API_URL, tenant_id: Optional[str] = None) -> Dict:
    """Ingest a log file (plain text, syslog, JSONL, CSV) into the backend for RCA analysis."""
    headers = {}
    if tenant_id:
        headers["X-Tenant-ID"] = tenant_id
    
    files = {"file": (filename, file_content, "application/octet-stream")}
    data = {}
    if file_type:
        data["file_type"] = file_type
    
    try:
        # Increase timeout for large files (50MB+ files may take longer)
        file_size_mb = len(file_content) / (1024 * 1024)
        timeout = max(300, int(file_size_mb * 10))  # At least 5 minutes, or 10 seconds per MB
        
        resp = requests.post(f"{api_url}/rca/ingest/logfile", files=files, data=data, headers=headers, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.Timeout:
        file_size_mb = len(file_content) / (1024 * 1024)
        return {"status": "error", "error": f"Upload timeout. File is {file_size_mb:.1f}MB. Try uploading via API directly or split the file."}
    except requests.exceptions.RequestException as e:
        error_msg = str(e)
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json().get('detail', error_msg)
                error_msg = f"{error_msg}: {error_detail}"
            except Exception:
                error_msg = f"{error_msg}: {e.response.text[:200]}"
        return {"status": "error", "error": error_msg}


def get_feature_flags(api_url: str = STRUCTURED_API_URL, tenant_id: Optional[str] = None) -> Dict:
    """Get feature flags for the current tenant."""
    headers = {}
    if tenant_id:
        headers["X-Tenant-ID"] = tenant_id
    try:
        resp = requests.get(f"{api_url}/features", headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException:
        # Default: all features enabled if API unavailable
        return {
            "tenant": tenant_id or "default",
            "features": {
                "rca_chat": True,
                "rca_ingest": True,
                "structured_rag": True,
                "agentic_rag": True,
                "multiagent_rag": True,
                "knowledge_base": True,
                "feedback": True,
            },
        }


def get_known_issues(api_url: str = STRUCTURED_API_URL) -> List[Dict[str, Any]]:
    """Get known issue templates for one-click RCA."""
    try:
        resp = requests.get(f"{api_url}/rca/known-issues", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get("known_issues", [])
    except requests.exceptions.RequestException:
        return []


def quick_rca_analysis(issue_id: str, api_url: str = STRUCTURED_API_URL, tenant_id: Optional[str] = None) -> Dict:
    """Perform one-click RCA for a known issue."""
    headers = {}
    if tenant_id:
        headers["X-Tenant-ID"] = tenant_id
    try:
        resp = requests.post(f"{api_url}/rca/quick/{issue_id}", headers=headers, timeout=120)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        return {
            "error": f"API Error: {str(e)}",
            "summary": "Unable to perform quick RCA analysis.",
            "rca_report": {},
            "citations": [],
        }


def is_feature_enabled(feature: str) -> bool:
    """Check if a feature is enabled for the current tenant."""
    flags = st.session_state.get("feature_flags", {})
    return flags.get("features", {}).get(feature, False)


def _extract_pdf_text(pdf_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    parts: list[str] = []
    for page in reader.pages:
        txt = page.extract_text() or ""
        txt = txt.strip()
        if txt:
            parts.append(txt)
    return "\n\n".join(parts).strip()


def _json_to_text(obj: object) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)

def format_guardrail_status(guardrail: Optional[Dict]) -> str:
    """Format guardrail status for display"""
    if not guardrail or guardrail.get("stage") == "none":
        return '<span class="status-badge status-success">✅ Safe</span>'
    
    if guardrail.get("blocked"):
        reason = guardrail.get("reason", "Unknown reason")
        return f'<span class="status-badge status-danger">🚫 Blocked: {reason}</span>'
    
    return '<span class="status-badge status-warning">⚠️ Filtered</span>'

# ============================================================================
# SIDEBAR - WORKFLOW SELECTOR & SETTINGS
# ============================================================================

with st.sidebar:
    st.title("RAG Console")
    st.markdown("---")

    # Tenant selection
    st.subheader("Tenant")
    tenant_input = st.text_input(
        "Tenant ID",
        value=st.session_state.get("tenant_id", TENANT_ID),
        help="Set tenant ID for feature flag checks. Use 'default' for default features.",
        key="tenant_input",
    )
    if tenant_input != st.session_state.get("tenant_id"):
        st.session_state.tenant_id = tenant_input
        # Reload feature flags when tenant changes
        st.session_state.feature_flags = {}
    
    # Load feature flags
    if not st.session_state.get("feature_flags"):
        with st.spinner("Loading features..."):
            flags = get_feature_flags(STRUCTURED_API_URL, st.session_state.tenant_id)
            st.session_state.feature_flags = flags
    
    st.markdown("---")

    st.subheader("Navigation")
    # Build navigation options based on feature flags
    nav_options = [NAV_CHAT, NAV_KB]
    if is_feature_enabled("rca_chat") or is_feature_enabled("rca_ingest"):
        nav_options.append(NAV_RCA)
    
    current_page = st.session_state.get("page", NAV_CHAT)
    if current_page not in nav_options:
        current_page = NAV_CHAT
    
    st.session_state.page = st.radio(
        "Page",
        options=nav_options,
        index=nav_options.index(current_page),
        label_visibility="collapsed",
    )
    
    if st.session_state.page == NAV_CHAT:
        # Workflow Selection
        st.markdown("---")
        st.subheader("Workflow")
        workflow_options = [
            WORKFLOW_STRUCTURED,
            WORKFLOW_AGENTIC,
            "Multi-agent (Auto)",
            "Multi-agent (Sequential)",
            "Multi-agent (Parallel)",
            "Multi-agent (Supervisor)",
        ]
        selected_workflow = st.radio(
            "Choose workflow:",
            workflow_options,
            index=workflow_options.index(st.session_state.workflow),
            key="workflow_selector"
        )
        st.session_state.workflow = selected_workflow
    elif st.session_state.page == NAV_KB:
        st.markdown("---")
        st.info("Knowledge Base Agent helps you ingest docs, inspect KB status, and answer questions with citations.")
    elif st.session_state.page == NAV_RCA:
        st.markdown("---")
        st.info("🔍 RCA Chat analyzes application errors, finds root causes, and generates actionable insights.")

    st.markdown("---")
    st.subheader("Inference mode")
    st.caption("Controls retrieval effort + verification strictness.")
    st.session_state.inference_mode = st.selectbox(
        "Mode",
        options=["balanced", "low", "high"],
        index=["balanced", "low", "high"].index(st.session_state.get("inference_mode", "balanced")),
        help="balanced: recommended default; low: higher recall; high: strictest grounding.",
    )
    
    # Workflow Description
    if st.session_state.page == NAV_CHAT:
        st.markdown("---")
        if st.session_state.workflow == WORKFLOW_STRUCTURED:
            st.info("Structured RAG: fixed pipeline, fast, predictable.")
        elif st.session_state.workflow == WORKFLOW_AGENTIC:
            st.info("Agentic RAG: tool-using flow, iterative refinement.")
        else:
            st.info("Multi-agent RAG: sequential / parallel / supervisor patterns.")
            # Multi-agent controls
            if st.session_state.workflow == "Multi-agent (Auto)":
                st.session_state["multiagent_auto_select"] = True
                st.session_state["multiagent_pattern"] = None
            elif st.session_state.workflow == "Multi-agent (Sequential)":
                st.session_state["multiagent_auto_select"] = False
                st.session_state["multiagent_pattern"] = "sequential"
            elif st.session_state.workflow == "Multi-agent (Parallel)":
                st.session_state["multiagent_auto_select"] = False
                st.session_state["multiagent_pattern"] = "parallel"
            else:
                st.session_state["multiagent_auto_select"] = False
                st.session_state["multiagent_pattern"] = "supervisor"

            with st.expander("Budgets (optional)", expanded=False):
                st.caption("Soft constraints using relative estimates. Lower budgets may downgrade to cheaper/faster patterns.")
                st.session_state["max_relative_cost"] = st.number_input(
                    "Max relative cost",
                    min_value=0.5,
                    max_value=10.0,
                    value=st.session_state.get("max_relative_cost", 2.0),
                    step=0.1,
                )
                st.session_state["max_relative_latency"] = st.number_input(
                    "Max relative latency",
                    min_value=0.5,
                    max_value=10.0,
                    value=st.session_state.get("max_relative_latency", 2.0),
                    step=0.1,
                )
    
    # API Status (compact)
    st.markdown("---")
    with st.expander("API status", expanded=False):
        structured_status = check_api_status(STRUCTURED_API_URL, "structured")
        agentic_status = check_api_status(AGENTIC_API_URL, "agentic")
        # Multi-agent runs on the structured server
        st.session_state.api_status["multiagent"] = structured_status

        def _badge(ok: bool, label: str) -> None:
            st.write(("✅ " if ok else "❌ ") + label)

        _badge(structured_status, "Backend (Structured/Multi-agent)")
        _badge(agentic_status, "Agentic endpoint")

    # Session Management
    st.markdown("---")
    if st.session_state.page == NAV_CHAT:
        st.subheader("Session")
        st.text(f"Session ID: {st.session_state.session_id[:8]}...")
        if st.button("New chat session", use_container_width=True):
            st.session_state.messages = []
            st.session_state.session_id = str(uuid.uuid4())
            st.rerun()
        if st.button("Clear chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    elif st.session_state.page == NAV_KB:
        st.subheader("KB Agent session")
        st.text(f"KB Session ID: {st.session_state.kb_session_id[:8]}...")
        if st.button("New KB session", use_container_width=True):
            st.session_state.kb_messages = []
            st.session_state.kb_session_id = str(uuid.uuid4())
            st.rerun()
        if st.button("Clear KB chat", use_container_width=True):
            st.session_state.kb_messages = []
            st.rerun()
    elif st.session_state.page == NAV_RCA:
        st.subheader("RCA session")
        st.text(f"RCA Session ID: {st.session_state.rca_session_id[:8]}...")
        if st.button("New RCA session", use_container_width=True):
            st.session_state.rca_messages = []
            st.session_state.rca_session_id = str(uuid.uuid4())
            st.rerun()
        if st.button("Clear RCA chat", use_container_width=True):
            st.session_state.rca_messages = []
            st.rerun()
    
    # Info
    st.markdown("---")
    st.markdown("""
    ### 📖 About
    This UI allows you to interact with both RAG workflows:
    - **Structured RAG**: Fixed pipeline, fast, predictable
    - **Agentic RAG**: Dynamic tool selection, iterative refinement
    """)

if st.session_state.page == NAV_CHAT:
    # ============================================================================
    # MAIN CHAT INTERFACE
    # ============================================================================
    st.title("Chat")
    st.caption(f"Workflow: {st.session_state.workflow}")

    chat_container = st.container()
    with chat_container:
        for idx, message in enumerate(st.session_state.messages):
            if message["role"] == "user":
                st.markdown(f"""
                <div class="user-message">
                    <strong>You:</strong><br>
                    {message["content"]}
                </div>
                """, unsafe_allow_html=True)
            else:
                guardrail_html = format_guardrail_status(message.get("guardrail"))
                workflow_badge = f'<span class="status-badge status-success">{message.get("workflow", "Unknown")}</span>'
                metadata = message.get("metadata") or {}
                meta_lines = []
                if isinstance(metadata, dict):
                    if metadata.get("pattern_selected"):
                        meta_lines.append(f"Pattern: {metadata.get('pattern_selected')}")
                    if metadata.get("selected_agent"):
                        meta_lines.append(f"Selected agent: {metadata.get('selected_agent')}")
                    if metadata.get("evaluation_scores"):
                        meta_lines.append("Scores: " + json.dumps(metadata.get("evaluation_scores"), ensure_ascii=False))
                    if metadata.get("pattern_selection_mode"):
                        meta_lines.append(f"Select mode: {metadata.get('pattern_selection_mode')}")
                    if metadata.get("inference_mode"):
                        meta_lines.append(f"Inference: {metadata.get('inference_mode')}")
                meta_html = ""
                if meta_lines:
                    meta_html = "<br><span style='color:#666; font-size:0.85rem;'>" + " | ".join(meta_lines) + "</span>"

                import html
                safe_content = html.escape(str(message["content"])).replace("\n", "<br>")
                st.markdown(f"""
                <div class="assistant-message">
                    <strong>Assistant:</strong> {workflow_badge} {guardrail_html}{meta_html}<br><br>
                    <div style="margin-top: 0.5rem;">{safe_content}</div>
                </div>
                """, unsafe_allow_html=True)

                citations = message.get("citations") or []
                if isinstance(citations, list) and len(citations) > 0:
                    with st.expander("Sources / citations", expanded=False):
                        for c in citations:
                            if not isinstance(c, dict):
                                continue
                            meta = c.get("metadata") or {}
                            label = meta.get("filename") or meta.get("source") or meta.get("doc_id") or "source"
                            chunk_id = meta.get("chunk_id")
                            start_index = meta.get("start_index")
                            header = f"{label}"
                            if chunk_id:
                                header += f" • {chunk_id}"
                            if start_index is not None:
                                header += f" • start={start_index}"
                            st.markdown(f"**{header}**")
                            st.code(str(c.get("text", ""))[:800])

                q_for_msg = message.get("question")
                if q_for_msg:
                    cols = st.columns([1, 1, 6])
                    up_key = f"fb_up_{idx}"
                    down_key = f"fb_down_{idx}"
                    if cols[0].button("👍", key=up_key):
                        result = send_feedback(question=q_for_msg, answer=str(message.get("content", "")), thumbs_up=True)
                        if result.get("status") == "ok":
                            cols[2].success("Feedback saved")
                        else:
                            cols[2].warning(f"Feedback not saved: {result.get('reason') or result.get('error')}")
                    if cols[1].button("👎", key=down_key):
                        st.session_state[f"show_fb_form_{idx}"] = True
                    if st.session_state.get(f"show_fb_form_{idx}", False):
                        with st.expander("Send correction (optional)", expanded=True):
                            comment = st.text_area("Comment", key=f"fb_comment_{idx}")
                            expected = st.text_area("Expected / corrected answer", key=f"fb_expected_{idx}")
                            if st.button("Submit feedback", key=f"fb_submit_{idx}"):
                                result = send_feedback(
                                    question=q_for_msg,
                                    answer=str(message.get("content", "")),
                                    thumbs_up=False,
                                    comment=comment or None,
                                    expected_answer=expected or None,
                                )
                                if result.get("status") == "ok":
                                    st.success("Feedback saved")
                                    st.session_state[f"show_fb_form_{idx}"] = False
                                else:
                                    st.warning(f"Feedback not saved: {result.get('reason') or result.get('error')}")

    st.markdown("---")
    user_input = st.chat_input("Ask a question…")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input, "timestamp": datetime.now().isoformat()})
        with st.spinner(f"Processing with {st.session_state.workflow}..."):
            if _is_multiagent_workflow(st.session_state.workflow):
                response = send_chat_message(
                    user_input,
                    st.session_state.workflow,
                    multiagent_pattern=st.session_state.get("multiagent_pattern"),
                    auto_select_pattern=bool(st.session_state.get("multiagent_auto_select", True)),
                    max_relative_cost=st.session_state.get("max_relative_cost"),
                    max_relative_latency=st.session_state.get("max_relative_latency"),
                )
            else:
                response = send_chat_message(user_input, st.session_state.workflow)
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": response.get("answer", "No answer received."),
                    "guardrail": response.get("guardrail"),
                    "metadata": response.get("metadata"),
                    "citations": response.get("citations"),
                    "question": user_input,
                    "workflow": st.session_state.workflow,
                    "timestamp": datetime.now().isoformat(),
                }
            )
        st.rerun()
elif st.session_state.page == NAV_KB:
    # ============================================================================
    # KNOWLEDGE BASE PAGE
    # ============================================================================
    st.title("Knowledge Base")
    st.caption("Ingest documents and chat with the Knowledge Base Agent. Citations appear when retrieval finds sources.")

    left, right = st.columns([0.46, 0.54], gap="large")

    with left:
        st.subheader("Ingest")
        uploaded_files = st.file_uploader(
            "Upload files",
            type=["pdf", "json", "txt", "md"],
            accept_multiple_files=True,
        )
        pasted_text = st.text_area("Or paste text", height=140, placeholder="Paste notes / docs here…")

        # Small preview
        if uploaded_files:
            with st.expander(f"Files selected ({len(uploaded_files)})", expanded=False):
                for f in uploaded_files:
                    st.write(f"- {getattr(f, 'name', 'uploaded')} ({len(f.getvalue())} bytes)")

        can_ingest = bool((pasted_text and pasted_text.strip()) or (uploaded_files and len(uploaded_files) > 0))
        if st.button("Ingest into knowledge base", type="primary", disabled=not can_ingest):
            texts: list[str] = []
            metadatas: list[dict] = []
            if pasted_text and pasted_text.strip():
                texts.append(pasted_text.strip())
                metadatas.append({"source": "pasted_text"})

            with st.spinner("Processing files…"):
                for f in uploaded_files or []:
                    filename = getattr(f, "name", "uploaded")
                    suffix = (filename.rsplit(".", 1)[-1] if "." in filename else "").lower()
                    raw = f.getvalue()
                    try:
                        if suffix == "pdf":
                            extracted = _extract_pdf_text(raw)
                            if extracted:
                                texts.append(extracted)
                                metadatas.append({"filename": filename, "type": "pdf"})
                            else:
                                st.warning(f"No extractable text found in PDF: {filename}")
                        elif suffix == "json":
                            obj = json.loads(raw.decode("utf-8", errors="ignore") or "{}")
                            if isinstance(obj, dict) and isinstance(obj.get("texts"), list):
                                j_texts = [str(x) for x in obj.get("texts") if str(x).strip()]
                                j_metas = obj.get("metadatas")
                                if isinstance(j_metas, list) and len(j_metas) == len(j_texts):
                                    for t, m in zip(j_texts, j_metas):
                                        texts.append(t)
                                        meta = m if isinstance(m, dict) else {}
                                        meta.setdefault("filename", filename)
                                        meta.setdefault("type", "json")
                                        metadatas.append(meta)
                                else:
                                    for t in j_texts:
                                        texts.append(t)
                                        metadatas.append({"filename": filename, "type": "json"})
                            else:
                                texts.append(_json_to_text(obj))
                                metadatas.append({"filename": filename, "type": "json"})
                        else:
                            text = raw.decode("utf-8", errors="ignore").strip()
                            if text:
                                texts.append(text)
                                metadatas.append({"filename": filename, "type": suffix or "text"})
                    except Exception as e:
                        st.error(f"Failed to process {filename}: {e}")

            if not texts:
                st.warning("Nothing to ingest.")
            else:
                with st.spinner("Ingesting…"):
                    result = ingest_texts(
                        texts=texts,
                        metadatas=metadatas,
                        api_url=STRUCTURED_API_URL,
                    )
                if result.get("status") == "success":
                    msg = f"Ingested {result.get('items_ingested')} items"
                    if hasattr(st, "toast"):
                        st.toast(msg)
                    st.success(msg)
                else:
                    st.error(f"Ingest failed: {result.get('error') or result}")

        st.markdown("---")
        st.subheader("Status & quick test")
        status = get_kb_status(STRUCTURED_API_URL)
        if status.get("status") == "error":
            st.error(status.get("error"))
            total_docs = 0
        else:
            total_docs = (status.get("vector_db") or {}).get("total_documents") or 0
        st.metric("Documents in vector DB", total_docs)
        with st.expander("Status details", expanded=False):
            st.json(status)

        test_q = st.text_input("Quick test question", value="What is in the knowledge base?", key="kb_test_q")
        if st.button("Run KB test"):
            with st.spinner("Querying…"):
                res = send_structured_chat(
                    test_q,
                    session_id=st.session_state.kb_session_id,
                    inference_mode=st.session_state.inference_mode,
                )
            st.write(res.get("answer"))
            cits = res.get("citations") or []
            if cits:
                with st.expander("Citations", expanded=True):
                    st.json(cits)

    with right:
        st.subheader("Knowledge Base Agent")
        st.caption("This agent always uses the Structured KB and will show citations when available.")
        for m in st.session_state.kb_messages:
            role = m.get("role", "assistant")
            with st.chat_message("user" if role == "user" else "assistant"):
                st.write(m.get("content", ""))
                if role != "user":
                    cits = m.get("citations") or []
                    if isinstance(cits, list) and cits:
                        with st.expander("Sources / citations", expanded=False):
                            for c in cits:
                                meta = (c or {}).get("metadata") or {}
                                label = meta.get("filename") or meta.get("source") or meta.get("doc_id") or "source"
                                st.markdown(f"**{label}**")
                                st.code(str((c or {}).get("text", ""))[:800])

        kb_input = st.chat_input("Ask the Knowledge Base Agent…")
        if kb_input:
            st.session_state.kb_messages.append({"role": "user", "content": kb_input})
            with st.spinner("Thinking…"):
                res = send_structured_chat(
                    kb_input,
                    session_id=st.session_state.kb_session_id,
                    inference_mode=st.session_state.inference_mode,
                )
            st.session_state.kb_messages.append(
                {"role": "assistant", "content": res.get("answer"), "citations": res.get("citations")}
            )
            st.rerun()

elif st.session_state.page == NAV_RCA:
    # ============================================================================
    # RCA CHAT PAGE
    # ============================================================================
    st.title("🔍 RCA Chat")
    st.caption("Root Cause Analysis chatbot for application errors. Upload error logs and analyze root causes automatically.")

    # Check feature flags
    rca_chat_enabled = is_feature_enabled("rca_chat")
    rca_ingest_enabled = is_feature_enabled("rca_ingest")
    
    if not rca_chat_enabled and not rca_ingest_enabled:
        st.error(f"❌ RCA features are not enabled for tenant '{st.session_state.tenant_id}'. Contact support to enable RCA features.")
        st.stop()

    tenant_id = st.session_state.tenant_id

    # One-Click RCA for Known Issues
    if rca_chat_enabled:
        st.markdown("---")
        st.subheader("⚡ One-Click RCA for Known Issues")
        st.caption("Quickly analyze common error patterns with predefined templates.")
        
        known_issues = get_known_issues(STRUCTURED_API_URL)
        if known_issues:
            # Create columns for issue cards
            cols = st.columns(min(len(known_issues), 5))
            for idx, issue in enumerate(known_issues):
                col_idx = idx % len(cols)
                with cols[col_idx]:
                    issue_icon = issue.get("icon", "🔍")
                    issue_name = issue.get("name", "Unknown")
                    issue_desc = issue.get("description", "")
                    issue_id = issue.get("id", "")
                    
                    # Create a button/card for each issue
                    button_key = f"quick_rca_{issue_id}"
                    if st.button(
                        f"{issue_icon} **{issue_name}**\n\n{issue_desc}",
                        key=button_key,
                        use_container_width=True,
                        help=f"Click to analyze: {issue.get('query', '')}",
                    ):
                        # Perform quick RCA
                        with st.spinner(f"Analyzing {issue_name}..."):
                            result = quick_rca_analysis(issue_id, STRUCTURED_API_URL, tenant_id)
                        
                        if result.get("error"):
                            st.error(result.get("error"))
                        else:
                            # Add to chat messages
                            st.session_state.rca_messages.append({
                                "role": "user",
                                "content": f"One-Click RCA: {issue_name} - {issue_desc}",
                            })
                            st.session_state.rca_messages.append({
                                "role": "assistant",
                                "content": result.get("summary", ""),
                                "rca_report": result.get("rca_report", {}),
                                "recommendations": result.get("recommendations", []),
                                "insights": result.get("insights", []),
                                "citations": result.get("citations", []),
                            })
                            st.rerun()
        else:
            st.info("No known issue templates available. Contact admin to configure templates.")

    st.markdown("---")

    left, right = st.columns([1, 1], gap="large")

    with left:
        st.subheader("Error log ingestion")
        if not rca_ingest_enabled:
            st.warning(f"⚠️ Error log ingestion is not enabled for tenant '{tenant_id}'.")
        else:
            st.caption("Upload error logs (JSON) or paste error details to build the knowledge base for RCA.")

        uploaded_error_file = st.file_uploader(
            "Upload error log file",
            type=["json", "jsonl", "log", "txt", "csv"],
            help="Supported formats:\n• JSON: Array of error objects\n• JSONL/NDJSON: One JSON object per line\n• Log files: Plain text, syslog format\n• CSV: Timestamp, level, message columns\n• TXT: Plain text error logs",
        )
        
        file_type_hint = None
        if uploaded_error_file:
            filename_lower = uploaded_error_file.name.lower()
            if filename_lower.endswith('.jsonl') or filename_lower.endswith('.ndjson'):
                file_type_hint = "jsonl"
            elif filename_lower.endswith('.csv'):
                file_type_hint = "csv"
            elif 'syslog' in filename_lower:
                file_type_hint = "syslog"
            elif filename_lower.endswith('.json'):
                file_type_hint = "json"
            else:
                file_type_hint = "text"

        st.markdown("**Or paste error details:**")
        error_message_input = st.text_area(
            "Error message",
            height=100,
            placeholder="Paste error message here...",
            key="rca_error_msg",
        )
        stack_trace_input = st.text_area(
            "Stack trace (optional)",
            height=150,
            placeholder="Paste full stack trace here...",
            key="rca_stack_trace",
        )
        timestamp_input = st.text_input(
            "Timestamp (optional, ISO format)",
            placeholder="2024-01-15T10:30:00Z",
            key="rca_timestamp",
        )

        if st.button("Ingest error log", type="primary", use_container_width=True, disabled=not rca_ingest_enabled):
            errors_to_ingest = []
            file_to_upload = None
            
            if uploaded_error_file:
                try:
                    filename_lower = uploaded_error_file.name.lower()
                    
                    # Show file info
                    file_size_mb = len(uploaded_error_file.getvalue()) / (1024 * 1024)
                    if file_size_mb > 10:
                        st.info(f"📄 File: {uploaded_error_file.name} ({file_size_mb:.1f} MB) - Processing large file, this may take a moment...")
                    
                    # Read file content
                    file_content = uploaded_error_file.read()
                    
                    if not file_content:
                        st.error("File appears to be empty. Please check the file and try again.")
                    else:
                        # Check if it's a JSON file (structured error format)
                        if filename_lower.endswith('.json'):
                            try:
                                content_str = file_content.decode("utf-8")
                                error_data = json.loads(content_str)
                                if isinstance(error_data, list):
                                    errors_to_ingest = error_data
                                elif isinstance(error_data, dict):
                                    errors_to_ingest = [error_data]
                                else:
                                    st.error("Invalid JSON format. Expected array of error objects or single error object.")
                            except json.JSONDecodeError:
                                # If JSON parsing fails, treat as log file
                                file_to_upload = (file_content, uploaded_error_file.name, file_type_hint)
                            except UnicodeDecodeError as e:
                                st.error(f"File encoding error: {e}. Trying to read as binary...")
                                file_to_upload = (file_content, uploaded_error_file.name, file_type_hint)
                            except Exception as e:
                                st.error(f"Failed to parse JSON: {e}")
                        else:
                            # Log file (text, jsonl, csv, syslog, etc.)
                            file_to_upload = (file_content, uploaded_error_file.name, file_type_hint)
                except Exception as e:
                    st.error(f"Error reading file: {str(e)}")
                    st.exception(e)
            elif error_message_input:
                error_obj = {"message": error_message_input}
                if stack_trace_input:
                    error_obj["stack_trace"] = stack_trace_input
                if timestamp_input:
                    error_obj["timestamp"] = timestamp_input
                errors_to_ingest = [error_obj]

            # Ingest based on type
            if file_to_upload:
                # Upload log file
                file_content, filename, file_type = file_to_upload
                with st.spinner(f"Parsing log file '{filename}' and ingesting errors…"):
                    result = ingest_log_file(
                        file_content=file_content,
                        filename=filename,
                        file_type=file_type,
                        api_url=STRUCTURED_API_URL,
                        tenant_id=tenant_id,
                    )
                if result.get("status") == "success":
                    items = result.get("items_ingested", 0)
                    msg = f"✅ Successfully ingested {items} error logs"
                    if hasattr(st, "toast"):
                        st.toast(msg)
                    st.success(msg)
                    
                    # Display detailed summary
                    file_info = result.get("file_info", {})
                    summary = result.get("summary", {})
                    
                    if file_info or summary:
                        with st.expander("📊 Upload Summary", expanded=True):
                            # File information
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("📄 File", file_info.get("filename", "Unknown"))
                            with col2:
                                st.metric("📏 Size", f"{file_info.get('file_size_mb', 0):.1f} MB")
                            with col3:
                                st.metric("🔍 Format", file_info.get("format", "auto-detected"))
                            
                            st.markdown("---")
                            
                            # Error statistics
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("🚨 Total Errors", summary.get("total_errors", 0))
                            with col2:
                                st.metric("📚 Documents Ingested", summary.get("total_documents_ingested", 0))
                            with col3:
                                stack_traces = summary.get("has_stack_traces", 0)
                                st.metric("📋 With Stack Traces", stack_traces)
                            
                            # Error types breakdown
                            error_types = summary.get("error_types", {})
                            if error_types:
                                st.markdown("**Top Error Types:**")
                                for error_type, count in list(error_types.items())[:5]:
                                    st.write(f"  • `{error_type}`: {count}")
                            
                            # Error levels
                            error_levels = summary.get("error_levels", {})
                            if error_levels:
                                st.markdown("**Error Levels:**")
                                level_cols = st.columns(len(error_levels))
                                for idx, (level, count) in enumerate(error_levels.items()):
                                    with level_cols[idx]:
                                        st.metric(level, count)
                            
                            # Timestamp range
                            timestamp_range = summary.get("timestamp_range", {})
                            if timestamp_range.get("earliest") or timestamp_range.get("latest"):
                                st.markdown("**Time Range:**")
                                col1, col2 = st.columns(2)
                                with col1:
                                    if timestamp_range.get("earliest"):
                                        st.caption(f"🕐 Earliest: {timestamp_range['earliest']}")
                                with col2:
                                    if timestamp_range.get("latest"):
                                        st.caption(f"🕐 Latest: {timestamp_range['latest']}")
                            
                            # Sample errors preview
                            sample_errors = summary.get("sample_errors", [])
                            if sample_errors:
                                st.markdown("**Sample Errors:**")
                                for idx, sample in enumerate(sample_errors[:3], 1):
                                    with st.container():
                                        st.markdown(f"**{idx}.** `{sample.get('type', 'Unknown')}`")
                                        st.caption(sample.get("message", "")[:150] + "..." if len(sample.get("message", "")) > 150 else sample.get("message", ""))
                                        if sample.get("timestamp"):
                                            st.caption(f"⏰ {sample['timestamp']}")
                                        st.markdown("---")
                else:
                    st.error(f"Ingest failed: {result.get('error') or result}")
            elif errors_to_ingest:
                # Ingest structured errors
                with st.spinner("Ingesting error logs…"):
                    result = ingest_errors(errors_to_ingest, api_url=STRUCTURED_API_URL, tenant_id=tenant_id)
                if result.get("status") == "success":
                    msg = f"✅ Ingested {result.get('items_ingested')} error logs"
                    if hasattr(st, "toast"):
                        st.toast(msg)
                    st.success(msg)
                else:
                    st.error(f"Ingest failed: {result.get('error') or result}")
            else:
                st.warning("Please upload a file or paste an error message.")

        st.markdown("---")
        st.subheader("Quick RCA analysis")
        if not rca_chat_enabled:
            st.warning(f"⚠️ RCA chat is not enabled for tenant '{tenant_id}'.")
        else:
            quick_error = st.text_area(
                "Error message to analyze",
                height=80,
                placeholder="Paste error message for quick RCA...",
                key="rca_quick_error",
            )
            include_trends = st.checkbox("Include trend analysis", value=True, help="May be slower but provides trend insights")
            if st.button("Analyze error", use_container_width=True):
                if quick_error:
                    with st.spinner("Running RCA analysis…"):
                        result = send_rca_chat(
                            error_message=quick_error,
                            include_trends=include_trends,
                            tenant_id=tenant_id,
                        )
                    if result.get("error"):
                        st.error(result.get("error"))
                    else:
                        st.session_state.rca_messages.append({
                            "role": "user",
                            "content": f"Error: {quick_error}",
                        })
                        st.session_state.rca_messages.append({
                            "role": "assistant",
                            "content": result.get("summary", ""),
                            "rca_report": result.get("rca_report", {}),
                            "recommendations": result.get("recommendations", []),
                            "insights": result.get("insights", []),
                            "citations": result.get("citations", []),
                        })
                        st.rerun()
                else:
                    st.warning("Please enter an error message.")

    with right:
        st.subheader("RCA Chat")
        if not rca_chat_enabled:
            st.warning(f"⚠️ RCA chat is not enabled for tenant '{tenant_id}'.")
        else:
            st.caption("Chat with the RCA agent to analyze errors and get root cause insights.")

        for idx, m in enumerate(st.session_state.rca_messages):
            role = m.get("role", "assistant")
            with st.chat_message("user" if role == "user" else "assistant"):
                col_content, col_action = st.columns([5, 1])
                
                with col_content:
                    st.write(m.get("content", ""))
                
                # Call to Ops button for both user and assistant messages
                with col_action:
                    call_to_ops_key = f"call_to_ops_{idx}"
                    if st.button("📞", key=call_to_ops_key, help="Call to Ops", use_container_width=True):
                        # Log the call to ops
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        message_content = m.get("content", "")[:200]
                        
                        # Get related context (previous message)
                        related_context = ""
                        if idx > 0:
                            prev_msg = st.session_state.rca_messages[idx - 1]
                            if prev_msg.get("role") != role:
                                related_context = prev_msg.get("content", "")[:200]
                        
                        # Build log entry
                        log_entry = f"[{timestamp}] 📞 CALL TO OPS\n"
                        log_entry += f"Message Type: {role.upper()}\n"
                        log_entry += f"Message: {message_content}\n"
                        if related_context:
                            log_entry += f"Related Context: {related_context}\n"
                        
                        if role == "assistant":
                            rca_report = m.get("rca_report", {})
                            if rca_report:
                                severity = rca_report.get("severity", "unknown")
                                root_cause = rca_report.get("root_cause", "N/A")[:200]
                                log_entry += f"Severity: {severity.upper()}\n"
                                log_entry += f"Root Cause: {root_cause}\n"
                        
                        log_entry += "---\n"
                        
                        st.session_state.rca_call_to_ops_logs.append(log_entry)
                        st.success("✅ Call to Ops logged")
                        st.rerun()
                
                # Display assistant-specific content
                if role == "assistant":
                    rca_report = m.get("rca_report", {})
                    if rca_report:
                        with st.expander("RCA Report", expanded=False):
                            st.json(rca_report)

                    recommendations = m.get("recommendations", [])
                    if recommendations:
                        st.markdown("**Recommended fixes:**")
                        for i, rec in enumerate(recommendations[:5], 1):
                            priority = rec.get("priority", "medium")
                            action = rec.get("action", rec.get("fix", ""))
                            st.markdown(f"{i}. **{priority.upper()}**: {action}")

                    insights = m.get("insights", [])
                    if insights:
                        st.markdown("**Key insights:**")
                        for insight in insights[:3]:
                            st.markdown(f"• {insight}")

                    citations = m.get("citations", [])
                    if isinstance(citations, list) and citations:
                        with st.expander("Similar errors / citations", expanded=False):
                            for c in citations[:3]:
                                meta = (c or {}).get("metadata") or {}
                                label = meta.get("source") or meta.get("filename") or "source"
                                st.markdown(f"**{label}**")
                                st.code(str((c or {}).get("text", ""))[:500])

        rca_input = st.chat_input("Paste error message or ask about an error…", disabled=not rca_chat_enabled)
        if rca_input and rca_chat_enabled:
            st.session_state.rca_messages.append({"role": "user", "content": rca_input})
            with st.spinner("Analyzing error…"):
                # Try to detect if it's an error message or a question
                is_error_message = any(
                    keyword in rca_input.lower()
                    for keyword in ["error", "exception", "failed", "failure", "traceback", "stack"]
                )

                if is_error_message:
                    result = send_rca_chat(
                        error_message=rca_input,
                        include_trends=include_trends,
                        tenant_id=tenant_id,
                    )
                else:
                    # Treat as a question about errors - use structured chat
                    result = send_structured_chat(
                        rca_input,
                        session_id=st.session_state.rca_session_id,
                        inference_mode=st.session_state.inference_mode,
                    )
                    # Convert to RCA format
                    result = {
                        "summary": result.get("answer", ""),
                        "rca_report": {},
                        "recommendations": [],
                        "insights": [],
                        "citations": result.get("citations", []),
                    }

            if result.get("error"):
                st.error(result.get("error"))
            else:
                st.session_state.rca_messages.append({
                    "role": "assistant",
                    "content": result.get("summary", ""),
                    "rca_report": result.get("rca_report", {}),
                    "recommendations": result.get("recommendations", []),
                    "insights": result.get("insights", []),
                    "citations": result.get("citations", []),
                })
            st.rerun()
        
        # Call to Ops Log Widget at bottom
        st.markdown("---")
        st.subheader("📞 Call to Ops Log")
        st.caption("Logs of all calls to operations team for escalation.")
        
        # Display logs in a text area (read-only)
        logs_text = "\n".join(st.session_state.rca_call_to_ops_logs) if st.session_state.rca_call_to_ops_logs else "No calls to ops logged yet."
        
        st.text_area(
            "Call to Ops Log",
            value=logs_text,
            height=200,
            disabled=True,
            help="This log tracks all calls to operations team. Logs are stored in session.",
            key="rca_call_to_ops_display",
        )
        
        # Clear logs button
        if st.session_state.rca_call_to_ops_logs:
            if st.button("🗑️ Clear Log", key="clear_ops_log", use_container_width=True):
                st.session_state.rca_call_to_ops_logs = []
                st.rerun()

# (footer removed)

