# 🚀 Deployment Guide - Free Hosting Options

This guide covers free hosting platforms for your RAG application (Structured + Agentic RAG with Streamlit UI).

## 📊 Your Application Architecture

- **Structured RAG API** (FastAPI) - Port 8000
- **Agentic RAG API** (FastAPI) - Port 8001  
- **Streamlit UI** - Port 8501
- **ChromaDB** - Vector database (local files)

---

## 🎯 Recommended Platforms (Free Tier)

### **Option 1: Streamlit Cloud + Render** ⭐ **RECOMMENDED**

**Why**: Easiest setup, best for your architecture

**Setup**:
- **Streamlit Cloud**: Hosts your UI (free, automatic deployments)
- **Render**: Hosts both FastAPI backends (free tier)

**Pros**:
- ✅ Streamlit Cloud is purpose-built for Streamlit apps
- ✅ Automatic deployments from GitHub
- ✅ Free tier is generous
- ✅ Render can host multiple services

**Cons**:
- ⚠️ Need to configure CORS for cross-origin requests
- ⚠️ Render free tier spins down after inactivity

**Cost**: **FREE**

---

### **Option 2: Railway** ⭐ **BEST FOR FULL STACK**

**Why**: Can host all services together, easy deployment

**Setup**:
- Host all 3 services (2 APIs + UI) on Railway
- Use Railway's internal networking

**Pros**:
- ✅ All services in one place
- ✅ Easy internal service communication
- ✅ Good free tier ($5 credit/month)
- ✅ Simple deployment from GitHub

**Cons**:
- ⚠️ Free tier has usage limits
- ⚠️ Need to manage multiple services

**Cost**: **FREE** (with $5/month credit)

---

### **Option 3: Fly.io**

**Why**: Good for containerized apps, generous free tier

**Setup**:
- Deploy each service as a separate Fly app
- Use Fly's private networking

**Pros**:
- ✅ Generous free tier
- ✅ Good performance
- ✅ Easy scaling

**Cons**:
- ⚠️ More complex setup
- ⚠️ Need Docker knowledge

**Cost**: **FREE** (with limits)

---

## 🚀 Quick Start: Streamlit Cloud + Render

### **Step 1: Prepare Your Repository**

Make sure your code is on GitHub.

### **Step 2: Deploy Backends on Render**

1. **Go to**: https://render.com
2. **Sign up** with GitHub
3. **Create 2 Web Services**:

#### **Service 1: Structured RAG API**

- **Name**: `rag-structured-api`
- **Environment**: Python 3
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `cd /opt/render/project/src && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Environment Variables**:
  - `OPENAI_API_KEY`: Your OpenAI key
  - `PORT`: Auto-set by Render

#### **Service 2: Agentic RAG API**

- **Name**: `rag-agentic-api`
- **Environment**: Python 3
- **Build Command**: `cd agentic && pip install -r ../requirements.txt`
- **Start Command**: `cd agentic && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Environment Variables**:
  - `OPENAI_API_KEY`: Your OpenAI key
  - `PORT`: Auto-set by Render

### **Step 3: Deploy UI on Streamlit Cloud**

1. **Go to**: https://streamlit.io/cloud
2. **Sign up** with GitHub
3. **New App**:
   - **Repository**: Your GitHub repo
   - **Branch**: `main`
   - **Main file**: `ui.py`
4. **Update `ui.py`** to use Render URLs (see config below)

### **Step 4: Update Configuration**

Update `ui.py` to use production URLs:

```python
# Production URLs (from Render)
STRUCTURED_API_URL = os.getenv("STRUCTURED_API_URL", "https://rag-structured-api.onrender.com")
AGENTIC_API_URL = os.getenv("AGENTIC_API_URL", "https://rag-agentic-api.onrender.com")
```

---

## 🚀 Quick Start: Railway (All-in-One)

### **Step 1: Install Railway CLI**

```bash
# macOS
brew install railway

# Or via npm
npm i -g @railway/cli
```

### **Step 2: Login and Initialize**

```bash
railway login
railway init
```

### **Step 3: Create Services**

Create 3 services:
1. Structured RAG API
2. Agentic RAG API  
3. Streamlit UI

### **Step 4: Configure**

Use Railway's dashboard to:
- Set environment variables
- Configure build commands
- Set start commands

---

## 📝 Deployment Files Needed

I'll create these files for you:

1. **`render.yaml`** - Render configuration
2. **`railway.json`** - Railway configuration
3. **`Procfile`** - For multiple process management
4. **`.streamlit/config.toml`** - Streamlit Cloud config
5. **`Dockerfile`** (optional) - For containerized deployment

---

## 🔧 Required Changes for Production

### **1. Update API URLs in UI**

```python
# ui.py - Use environment variables
import os

STRUCTURED_API_URL = os.getenv(
    "STRUCTURED_API_URL", 
    "http://localhost:8000"  # Default for local
)
AGENTIC_API_URL = os.getenv(
    "AGENTIC_API_URL",
    "http://localhost:8001"  # Default for local
)
```

### **2. Add CORS to FastAPI**

```python
# app/main.py and agentic/app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### **3. Handle ChromaDB Persistence**

For production, consider:
- Using external vector DB (Pinecone, Weaviate)
- Or persisting ChromaDB to cloud storage

---

## 🎯 My Recommendation

**For Quick Start**: **Streamlit Cloud + Render**
- Easiest to set up
- Free tier is sufficient
- Automatic deployments

**For Production**: **Railway**
- Better for managing all services
- More control
- Better performance

---

## 📋 Next Steps

1. Choose your platform
2. I'll create the deployment files
3. Follow platform-specific setup
4. Deploy!

**Which platform would you like to use?** I can create the specific configuration files for your choice.

