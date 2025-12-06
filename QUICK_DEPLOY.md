# 🚀 Quick Deployment Guide

## Recommended: Streamlit Cloud + Render (Easiest)

### **Step 1: Deploy APIs on Render** (5 minutes)

1. Go to https://render.com and sign up with GitHub

2. **Create First Service - Structured RAG API:**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Settings:
     - **Name**: `rag-structured-api`
     - **Root Directory**: `/` (root)
     - **Environment**: `Python 3`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Environment Variables**:
     - `OPENAI_API_KEY`: (your key)
   - Click "Create Web Service"

3. **Create Second Service - Agentic RAG API:**
   - Click "New +" → "Web Service"
   - Connect same GitHub repository
   - Settings:
     - **Name**: `rag-agentic-api`
     - **Root Directory**: `/agentic`
     - **Environment**: `Python 3`
     - **Build Command**: `pip install -r ../requirements.txt`
     - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Environment Variables**:
     - `OPENAI_API_KEY`: (your key)
   - Click "Create Web Service"

4. **Wait for deployment** (5-10 minutes)
   - Note the URLs: `https://rag-structured-api.onrender.com` and `https://rag-agentic-api.onrender.com`

### **Step 2: Deploy UI on Streamlit Cloud** (3 minutes)

1. Go to https://streamlit.io/cloud and sign up with GitHub

2. Click "New app"

3. Settings:
   - **Repository**: Your GitHub repo
   - **Branch**: `main`
   - **Main file**: `ui.py`

4. **Add Secrets** (click "Advanced settings" → "Secrets"):
   ```toml
   STRUCTURED_API_URL = "https://rag-structured-api.onrender.com"
   AGENTIC_API_URL = "https://rag-agentic-api.onrender.com"
   ```

5. Click "Deploy"

6. **Your app will be live at**: `https://your-app-name.streamlit.app`

### **Step 3: Test**

1. Visit your Streamlit app URL
2. Try asking a question
3. Check both Structured and Agentic RAG workflows

---

## Alternative: Railway (All-in-One)

### **Step 1: Install Railway CLI**

```bash
npm i -g @railway/cli
# Or
brew install railway
```

### **Step 2: Deploy**

```bash
railway login
railway init
railway up
```

Railway will detect your services and deploy them automatically.

---

## ⚠️ Important Notes

1. **Free Tier Limitations**:
   - Render: Services spin down after 15 min inactivity (first request takes ~30s)
   - Streamlit Cloud: Free tier is generous
   - Railway: $5/month credit

2. **ChromaDB Persistence**:
   - Current setup uses local files
   - For production, consider:
     - Cloud storage (S3, GCS) for `ragdb/` folder
     - Or use managed vector DB (Pinecone, Weaviate)

3. **Environment Variables**:
   - Never commit `.env` file
   - Set all secrets in platform dashboards

4. **CORS**:
   - Already configured in both APIs
   - For production, update `allow_origins` to specific domains

---

## 🎉 You're Live!

Once deployed, share your Streamlit app URL with others!

**Need help?** Check the full `DEPLOYMENT_GUIDE.md` for detailed instructions.

