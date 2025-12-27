# File Upload Fix for Large Files

## Issue
UI was not uploading large files (50MB+) like `catalina.part.bo.log`.

## Fixes Applied

### 1. Streamlit Configuration
Created `.streamlit/config.toml` with increased upload limits:
```toml
[server]
maxUploadSize = 200  # MB
maxMessageSize = 200  # MB
```

**Note:** You need to **restart Streamlit** for this to take effect!

### 2. Improved Error Handling
- Added file size display for large files (>10MB)
- Better error messages with details
- Increased timeout for large file uploads (10 seconds per MB, minimum 5 minutes)
- Better exception handling

### 3. File Reading Improvements
- Check for empty files
- Better encoding error handling
- Progress indication for large files

## How to Use

### Option 1: Via UI (After Restart)
1. **Restart Streamlit UI** (the config change requires restart)
2. Go to **RCA Chat** page
3. Upload `catalina.part.bo.log` (or any log file)
4. Click "Ingest error log"
5. Wait for processing (large files may take a few minutes)

### Option 2: Via API (Works Now)
```bash
curl -X POST http://localhost:8000/rca/ingest/logfile \
  -F "file=@/Users/sachin/v2/psuedop/A1/logs/catalina.part.bo.log" \
  -F "file_type=text"
```

## Verification

Check if file was ingested:
```bash
curl "http://localhost:8000/rca/check-file/catalina.part.bo.log"
```

## Current Status

✅ **API upload works** - Successfully ingested `catalina.part.bo.log` (12 errors found)
✅ **Streamlit config created** - Upload limit set to 200MB
⚠️ **UI needs restart** - Streamlit must be restarted for config to take effect

## Next Steps

1. **Restart Streamlit UI**:
   ```bash
   # Stop current Streamlit
   pkill -f streamlit
   
   # Start again
   cd /Users/sachin/nltk_data/api
   streamlit run ui.py
   ```

2. Try uploading the file again via UI

3. If still having issues, use the API method (which is confirmed working)

