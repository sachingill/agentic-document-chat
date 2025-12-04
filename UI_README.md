# 🎨 RAG Chat UI - User Guide

A simple, elegant, and intuitive Streamlit-based UI for interacting with both Structured and Agentic RAG workflows.

## 📸 Screenshot

![RAG Chat UI](ui_screenshot.png)

The UI features:
- **Left Sidebar**: Workflow selection, API status, session management
- **Main Chat Area**: Clean conversation interface with user and assistant messages
- **Status Badges**: Visual indicators for workflow type and guardrail status
- **Real-time Updates**: Live API status monitoring

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install streamlit requests
# Or install all requirements
pip install -r requirements.txt
```

### 2. Start the Backend Servers

**Terminal 1 - Structured RAG:**
```bash
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Agentic RAG:**
```bash
cd agentic
uvicorn app.main:app --reload --port 8001
```

### 3. Launch the UI

**Terminal 3 - Streamlit UI:**
```bash
streamlit run ui.py
```

The UI will open automatically in your browser at `http://localhost:8501`

## 🎯 Features

### ✨ Workflow Selection
- **Structured RAG**: Fixed pipeline, fast, predictable
- **Agentic RAG**: Dynamic tool selection, iterative refinement

### 💬 Chat Interface
- Clean, modern chat UI
- Conversation history
- Real-time API status monitoring
- Guardrail status indicators

### 🔒 Safety Features
- Visual guardrail status (Safe/Blocked/Filtered)
- Input/output safety checks displayed
- Clear error messages

### 📊 Session Management
- Unique session IDs
- New session button
- Clear chat history
- Persistent conversation context

## 🎨 UI Components

### Sidebar
- **Workflow Selector**: Switch between Structured and Agentic RAG
- **API Status**: Real-time connection status for both APIs
- **Session Info**: Current session ID and management buttons
- **Documentation**: Quick reference guide

### Main Chat Area
- **Message Display**: User and assistant messages with styling
- **Status Badges**: Workflow type and guardrail status
- **Chat Input**: Type your questions at the bottom

## 📝 Usage Examples

### Example 1: Simple Question (Structured RAG)
```
You: What is circuit breaker?
Assistant: [Structured RAG] ✅ Safe
Circuit breakers are safety devices that automatically interrupt...
```

### Example 2: Complex Question (Agentic RAG)
```
You: Compare circuit breaker and load balancing
Assistant: [Agentic RAG] ✅ Safe
[Agentic RAG will use multiple tool calls to gather information]
```

## 🔧 Configuration

### API URLs
Edit `ui.py` to change API endpoints:
```python
STRUCTURED_API_URL = "http://localhost:8000"
AGENTIC_API_URL = "http://localhost:8001"
```

### Customization
- Modify CSS in the `st.markdown()` section for custom styling
- Adjust timeout values in `send_chat_message()` function
- Customize workflow descriptions in the sidebar

## 🐛 Troubleshooting

### API Not Connecting
- Ensure both backend servers are running
- Check API URLs in `ui.py`
- Verify ports 8000 and 8001 are available

### UI Not Loading
- Check Streamlit installation: `streamlit --version`
- Ensure all dependencies are installed
- Check for port conflicts (default: 8501)

### Messages Not Appearing
- Check browser console for errors
- Verify API responses in backend logs
- Try clearing chat and starting a new session

## 🎨 Design Philosophy

The UI is designed to be:
- **Simple**: Clean interface, no clutter
- **Elegant**: Modern gradient design, smooth interactions
- **Intuitive**: Clear workflow selection, obvious actions
- **Informative**: Status indicators, guardrail feedback

## 📚 Next Steps

- Add file upload for document ingestion
- Implement conversation export
- Add response time metrics
- Include token usage statistics
- Add dark mode toggle

---

**Enjoy chatting with your RAG system!** 🚀

