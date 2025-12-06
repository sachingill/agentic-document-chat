# 🔐 Environment Variables Setup Guide

This guide explains how to set environment variables securely on different hosting platforms.

## ⚠️ Security Best Practices

- ✅ **NEVER commit `.env` files to git**
- ✅ **Set environment variables on the hosting platform**
- ✅ **Use platform secrets management**
- ✅ **Rotate keys regularly**

---

## 📋 Required Environment Variables

### **For Both APIs (Structured & Agentic RAG)**

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `OPENAI_API_KEY` | ✅ **Yes** | Your OpenAI API key | `sk-...` |
| `LANGSMITH_API_KEY` | ❌ Optional | LangSmith API key for tracing | `lsv2_...` |
| `LANGSMITH_TRACING` | ❌ Optional | Enable LangSmith tracing | `true` or `false` |
| `LANGSMITH_PROJECT` | ❌ Optional | LangSmith project name | `rag-api` |

### **For Agentic RAG API Only**

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `AGENTIC_MAX_ITERATIONS` | ❌ Optional | Max iterations for agentic loop | `3` |
| `AGENTIC_MAX_CONTEXT_DOCS` | ❌ Optional | Max context documents | `15` |

### **For Streamlit UI**

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `STRUCTURED_API_URL` | ✅ **Yes** | URL of Structured RAG API | `https://rag-structured-api.onrender.com` |
| `AGENTIC_API_URL` | ✅ **Yes** | URL of Agentic RAG API | `https://rag-agentic-api.onrender.com` |

---

## 🚀 Platform-Specific Setup

### **1. Render.com**

#### **For Each API Service:**

1. Go to your service dashboard on Render
2. Click **"Environment"** tab
3. Click **"Add Environment Variable"**
4. Add each variable:
   - **Key**: `OPENAI_API_KEY`
   - **Value**: Your actual API key
   - Click **"Save Changes"**

5. Repeat for other variables:
   - `LANGSMITH_API_KEY` (optional)
   - `LANGSMITH_TRACING` (optional)
   - `AGENTIC_MAX_ITERATIONS` (for agentic API only)
   - `AGENTIC_MAX_CONTEXT_DOCS` (for agentic API only)

#### **Screenshot Guide:**
```
Service Dashboard → Environment → Add Environment Variable
```

**Note**: Render automatically sets `PORT` variable - don't override it.

---

### **2. Streamlit Cloud**

#### **For Streamlit UI:**

1. Go to your app on Streamlit Cloud
2. Click **"Settings"** (⚙️ icon)
3. Click **"Secrets"** tab
4. Add secrets in TOML format:

```toml
STRUCTURED_API_URL = "https://rag-structured-api.onrender.com"
AGENTIC_API_URL = "https://rag-agentic-api.onrender.com"
```

5. Click **"Save"**

**Note**: Streamlit Cloud doesn't need API keys - those are handled by the backend APIs.

---

### **3. Railway**

#### **For Each Service:**

1. Go to your project on Railway
2. Click on the service
3. Click **"Variables"** tab
4. Click **"New Variable"**
5. Add each variable:
   - **Key**: `OPENAI_API_KEY`
   - **Value**: Your actual API key
   - Click **"Add"**

6. Repeat for other variables

**Note**: Railway automatically sets `PORT` variable.

---

### **4. Fly.io**

#### **Using Fly CLI:**

```bash
# Set environment variable
fly secrets set OPENAI_API_KEY=your-key-here

# Set multiple at once
fly secrets set \
  OPENAI_API_KEY=your-key \
  LANGSMITH_API_KEY=your-langsmith-key
```

#### **Or via Dashboard:**

1. Go to your app on Fly.io
2. Click **"Secrets"** tab
3. Click **"Add Secret"**
4. Add key-value pairs

---

## 🔍 Verifying Environment Variables

### **Test API Endpoints:**

After deployment, test that environment variables are set:

```bash
# Test Structured API
curl https://your-structured-api.onrender.com/

# Test Agentic API
curl https://your-agentic-api.onrender.com/
```

If you see error messages about missing `OPENAI_API_KEY`, the environment variable wasn't set correctly.

---

## 🛠️ Local Development

For local development, you can use a `.env` file (which is gitignored):

```bash
# Create .env file (not committed to git)
cat > .env << EOF
OPENAI_API_KEY=your-key-here
LANGSMITH_API_KEY=your-langsmith-key
LANGSMITH_TRACING=false
EOF
```

**Note**: The code will automatically load `.env` if it exists locally, but won't require it in production.

---

## 🔄 Updating Environment Variables

### **Render:**
1. Go to service → Environment tab
2. Edit existing variable or add new one
3. Click "Save Changes"
4. Service will automatically redeploy

### **Streamlit Cloud:**
1. Go to app → Settings → Secrets
2. Edit secrets file
3. Click "Save"
4. App will automatically redeploy

### **Railway:**
1. Go to service → Variables tab
2. Edit or add variables
3. Changes apply immediately (no redeploy needed)

---

## 🚨 Troubleshooting

### **Error: "OPENAI_API_KEY not found"**

**Cause**: Environment variable not set on hosting platform

**Solution**:
1. Check platform dashboard
2. Verify variable name is exactly `OPENAI_API_KEY` (case-sensitive)
3. Ensure no extra spaces
4. Redeploy service

### **Error: "Connection refused" in UI**

**Cause**: API URLs not set correctly in Streamlit

**Solution**:
1. Check Streamlit Cloud secrets
2. Verify API URLs are correct (include `https://`)
3. Ensure APIs are deployed and running

### **Error: "CORS error"**

**Cause**: CORS not configured (should be fixed in code)

**Solution**: Already handled in code - CORS middleware is configured

---

## 📝 Quick Checklist

Before deploying:

- [ ] `OPENAI_API_KEY` set on both API services
- [ ] `STRUCTURED_API_URL` set on Streamlit UI
- [ ] `AGENTIC_API_URL` set on Streamlit UI
- [ ] Optional: `LANGSMITH_API_KEY` if using tracing
- [ ] `.env` file is in `.gitignore` (already done)
- [ ] No secrets committed to git

---

## 🔐 Security Reminders

1. **Never commit API keys to git**
2. **Use platform secrets management**
3. **Rotate keys if exposed**
4. **Use different keys for dev/prod**
5. **Monitor API usage regularly**

---

## 📚 Additional Resources

- [Render Environment Variables](https://render.com/docs/environment-variables)
- [Streamlit Cloud Secrets](https://docs.streamlit.io/streamlit-community-cloud/get-started/deploy-an-app#secrets-management)
- [Railway Environment Variables](https://docs.railway.app/develop/variables)
- [Fly.io Secrets](https://fly.io/docs/reference/secrets/)

