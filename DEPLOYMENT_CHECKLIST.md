# ✅ Deployment Checklist

Use this checklist to ensure secure deployment.

## 🔐 Security Checklist

- [ ] `.env` file is in `.gitignore` (already done ✅)
- [ ] No API keys committed to git
- [ ] Environment variables will be set on hosting platform (not in code)
- [ ] `.env.example` created as template (no real values)

## 📝 Pre-Deployment

- [ ] Code is pushed to GitHub
- [ ] All deployment files are committed:
  - [ ] `render.yaml` (for Render)
  - [ ] `Procfile` (for Railway/Heroku)
  - [ ] `Dockerfile` (optional)
  - [ ] `.streamlit/config.toml` (for Streamlit Cloud)
- [ ] `ui.py` uses environment variables for API URLs
- [ ] CORS is configured in both FastAPI apps

## 🚀 Deployment Steps

### **Step 1: Deploy APIs on Render**

- [ ] Sign up at https://render.com
- [ ] Create first service: Structured RAG API
- [ ] Create second service: Agentic RAG API
- [ ] **Set environment variables in Render dashboard:**
  - [ ] `OPENAI_API_KEY` (REQUIRED)
  - [ ] `LANGSMITH_API_KEY` (optional)
  - [ ] `LANGSMITH_TRACING` (optional)
- [ ] Wait for deployment to complete
- [ ] Note the API URLs:
  - [ ] Structured API: `https://rag-structured-api.onrender.com`
  - [ ] Agentic API: `https://rag-agentic-api.onrender.com`

### **Step 2: Deploy UI on Streamlit Cloud**

- [ ] Sign up at https://streamlit.io/cloud
- [ ] Connect GitHub repository
- [ ] Create new app
- [ ] **Set secrets in Streamlit Cloud:**
  - [ ] `STRUCTURED_API_URL` = your Render API URL
  - [ ] `AGENTIC_API_URL` = your Render API URL
- [ ] Deploy app
- [ ] Note your app URL: `https://your-app.streamlit.app`

### **Step 3: Test Deployment**

- [ ] Visit Streamlit app URL
- [ ] Test Structured RAG workflow
- [ ] Test Agentic RAG workflow
- [ ] Verify no errors in console
- [ ] Check API endpoints are accessible

## 🔍 Post-Deployment Verification

- [ ] APIs respond to health checks
- [ ] UI can connect to both APIs
- [ ] No CORS errors in browser console
- [ ] Environment variables are set correctly
- [ ] No API keys visible in code/logs

## 📚 Documentation

- [ ] Read `ENVIRONMENT_VARIABLES.md` for detailed setup
- [ ] Read `QUICK_DEPLOY.md` for step-by-step guide
- [ ] Read `DEPLOYMENT_GUIDE.md` for platform details

---

## 🎉 You're Live!

Once all checkboxes are complete, your app is deployed and ready to share!

**Share your app**: `https://your-app.streamlit.app`

