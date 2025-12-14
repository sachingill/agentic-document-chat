"""
RAG Chat UI - Streamlit Application

A simple, elegant, and intuitive UI for both Structured and Agentic RAG workflows.
"""

import streamlit as st
import requests
import json
import os
from typing import Dict, List, Optional
from datetime import datetime
import uuid

# ============================================================================
# CONFIGURATION
# ============================================================================
# Use environment variables for production, fallback to localhost for development

STRUCTURED_API_URL = os.getenv("STRUCTURED_API_URL", "http://localhost:8000")
AGENTIC_API_URL = os.getenv("AGENTIC_API_URL", "http://localhost:8001")

WORKFLOW_STRUCTURED = "Structured RAG"
WORKFLOW_AGENTIC = "Agentic RAG"

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
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "workflow" not in st.session_state:
    st.session_state.workflow = WORKFLOW_STRUCTURED  # Default

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

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
    st.title("🤖 RAG Chat")
    st.markdown("---")
    
    # Workflow Selection
    st.subheader("📋 Workflow")
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
    
    # Workflow Description
    st.markdown("---")
    if selected_workflow == WORKFLOW_STRUCTURED:
        st.info("""
        **Structured RAG**
        - Fixed pipeline flow
        - Fast & predictable
        - Best for simple questions
        """)
    elif selected_workflow == WORKFLOW_AGENTIC:
        st.info("""
        **Agentic RAG**
        - Dynamic tool selection
        - Iterative refinement
        - Best for complex questions
        """)
    else:
        st.info("""
        **Multi-agent RAG**
        - Multiple patterns (sequential / parallel / supervisor-worker)
        - Auto-select can choose a pattern per question
        - Parallel includes evaluation to pick the best answer
        """)
        
        # Multi-agent controls
        st.markdown("**Multi-agent Settings**")
        if selected_workflow == "Multi-agent (Auto)":
            st.session_state["multiagent_auto_select"] = True
            st.session_state["multiagent_pattern"] = None
        elif selected_workflow == "Multi-agent (Sequential)":
            st.session_state["multiagent_auto_select"] = False
            st.session_state["multiagent_pattern"] = "sequential"
        elif selected_workflow == "Multi-agent (Parallel)":
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
    
    # API Status
    st.markdown("---")
    st.subheader("🔌 API Status")
    
    structured_status = check_api_status(STRUCTURED_API_URL, "structured")
    agentic_status = check_api_status(AGENTIC_API_URL, "agentic")
    # Multi-agent runs on the structured server
    st.session_state.api_status["multiagent"] = structured_status
    
    if structured_status:
        st.success("✅ Structured RAG API: Online")
    else:
        st.error("❌ Structured RAG API: Offline")
    
    if agentic_status:
        st.success("✅ Agentic RAG API: Online")
    else:
        st.error("❌ Agentic RAG API: Offline")
    
    if structured_status:
        st.success("✅ Multi-agent API: Online (via Structured server)")
    else:
        st.error("❌ Multi-agent API: Offline (Structured server down)")
    
    # Session Management
    st.markdown("---")
    st.subheader("💬 Session")
    st.text(f"Session ID: {st.session_state.session_id[:8]}...")
    
    if st.button("🔄 New Session", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()
    
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    # Info
    st.markdown("---")
    st.markdown("""
    ### 📖 About
    This UI allows you to interact with both RAG workflows:
    - **Structured RAG**: Fixed pipeline, fast, predictable
    - **Agentic RAG**: Dynamic tool selection, iterative refinement
    """)

# ============================================================================
# MAIN CHAT INTERFACE
# ============================================================================

st.title("💬 RAG Chat Interface")
st.markdown(f"**Current Workflow:** {st.session_state.workflow}")

# Display chat messages
chat_container = st.container()

with chat_container:
    for message in st.session_state.messages:
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
            meta_html = ""
            if meta_lines:
                meta_html = "<br><span style='color:#666; font-size:0.85rem;'>" + " | ".join(meta_lines) + "</span>"
            
            # Escape HTML in message content to prevent issues
            import html
            safe_content = html.escape(str(message["content"]))
            # Convert newlines to <br> for proper display
            safe_content = safe_content.replace('\n', '<br>')
            
            st.markdown(f"""
            <div class="assistant-message">
                <strong>Assistant:</strong> {workflow_badge} {guardrail_html}{meta_html}<br><br>
                <div style="margin-top: 0.5rem;">{safe_content}</div>
            </div>
            """, unsafe_allow_html=True)

# Chat input
st.markdown("---")
user_input = st.chat_input("Ask a question...")

if user_input:
    # Add user message to chat
    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
        "timestamp": datetime.now().isoformat()
    })
    
    # Show loading indicator
    with st.spinner(f"Processing with {st.session_state.workflow}..."):
        # Send to API
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
        
        # Extract answer and guardrail info
        answer = response.get("answer", "No answer received.")
        guardrail = response.get("guardrail")
        metadata = response.get("metadata")
        
        # Add assistant message to chat
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "guardrail": guardrail,
            "metadata": metadata,
            "workflow": st.session_state.workflow,
            "timestamp": datetime.now().isoformat()
        })
    
    # Rerun to update UI
    st.rerun()

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>RAG Chat Interface | Built with Streamlit</p>
</div>
""", unsafe_allow_html=True)

