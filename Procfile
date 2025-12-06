# Procfile for multi-process deployment (Railway, Heroku, etc.)
# Note: For Render, use render.yaml instead

# Structured RAG API
structured: cd /opt/render/project/src && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}

# Agentic RAG API  
agentic: cd agentic && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8001}

# Streamlit UI (if hosting on same platform)
web: streamlit run ui.py --server.port=${PORT:-8501} --server.address=0.0.0.0

