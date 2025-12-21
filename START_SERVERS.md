# 🚀 How to Start All Services

## Quick Start Guide

You need **2 terminals** to run everything:

### Terminal 1: Backend API (Port 8000)

```bash
cd /Users/sachin/nltk_data/api
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**Verify it's running:**
```bash
curl http://localhost:8000/
# Should return: {"message":"API is running"}
```

### Terminal 2: Streamlit UI (Port 8501)

```bash
cd /Users/sachin/nltk_data/api
source venv/bin/activate
streamlit run ui.py
```

The UI will automatically open at `http://localhost:8501`

---

## Troubleshooting

### Port 8001 Not Working

**Check if server is running:**
```bash
lsof -i :8001
# If nothing shows, the server isn't running
```

**Check for errors:**
- Make sure `.env` file exists in `/Users/sachin/nltk_data/api/` with `OPENAI_API_KEY`
- Check terminal output for import errors
- Verify virtual environment is activated

### UI Not Loading

**Check if Streamlit is installed:**
```bash
pip install streamlit requests
```

**Check if port 8501 is available:**
```bash
lsof -i :8501
```

**Start UI manually:**
```bash
cd /Users/sachin/nltk_data/api
source venv/bin/activate
streamlit run ui.py
```

**Check browser console:**
- Open browser developer tools (F12)
- Check Console tab for errors
- Check Network tab to see if API calls are failing

### Common Issues

1. **"Module not found" errors:**
   - Make sure virtual environment is activated
   - Run: `pip install -r requirements.txt`

2. **"OPENAI_API_KEY not found":**
   - Create `.env` file in project root
   - Add: `OPENAI_API_KEY=your-key-here`

3. **Port already in use:**
   - Kill process using the port: `lsof -ti:8001 | xargs kill -9`
   - Or use different ports

---

## One-Command Startup (Future Enhancement)

You can create a script to start all services at once, but for now, use 3 separate terminals as shown above.

