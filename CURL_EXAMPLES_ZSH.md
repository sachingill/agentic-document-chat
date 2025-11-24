# Curl Examples for zsh Terminal

## Common Issues in zsh

zsh has some quirks with curl commands, especially for file uploads:

1. **`@` symbol interpretation**: zsh may interpret `@` in file paths
2. **File path quoting**: Paths with spaces or special characters need quoting
3. **Multiple file uploads**: Syntax differs slightly from bash

---

## `/agent/ingest` Endpoint - File Upload

### Single File Upload

**❌ Problematic (may fail in zsh):**
```bash
curl -X POST "http://localhost:8000/agent/ingest" \
  -F "files=@test_doc.txt"
```

**✅ Correct for zsh (Option 1 - Quote the entire value):**
```bash
curl -X POST "http://localhost:8000/agent/ingest" \
  -F "files=@test_doc.txt"
```

**✅ Correct for zsh (Option 2 - Use full path):**
```bash
curl -X POST "http://localhost:8000/agent/ingest" \
  -F "files=@$(pwd)/test_doc.txt"
```

**✅ Correct for zsh (Option 3 - Escape or quote):**
```bash
curl -X POST "http://localhost:8000/agent/ingest" \
  -F 'files=@test_doc.txt'
```

### Multiple File Upload

**✅ Correct syntax for multiple files:**
```bash
curl -X POST "http://localhost:8000/agent/ingest" \
  -F "files=@test_doc.txt" \
  -F "files=@test_doc2.txt"
```

**✅ With full paths:**
```bash
curl -X POST "http://localhost:8000/agent/ingest" \
  -F "files=@/absolute/path/to/file1.txt" \
  -F "files=@/absolute/path/to/file2.txt"
```

**✅ With relative paths (using pwd):**
```bash
curl -X POST "http://localhost:8000/agent/ingest" \
  -F "files=@$(pwd)/test_doc.txt" \
  -F "files=@$(pwd)/test_doc2.txt"
```

### Files with Spaces in Names

**✅ Quote the file path:**
```bash
curl -X POST "http://localhost:8000/agent/ingest" \
  -F "files=@\"My Document.txt\""
```

Or use full path:
```bash
curl -X POST "http://localhost:8000/agent/ingest" \
  -F "files=@/Users/username/Documents/My Document.txt"
```

---

## Troubleshooting

### Issue: "No such file or directory"

**Problem:** File path not found

**Solutions:**
1. Use absolute paths:
   ```bash
   curl -X POST "http://localhost:8000/agent/ingest" \
     -F "files=@/Users/sachin/nltk_data/api/test_doc.txt"
   ```

2. Check current directory:
   ```bash
   pwd
   ls -la test_doc.txt
   ```

3. Use `$(pwd)` for relative paths:
   ```bash
   curl -X POST "http://localhost:8000/agent/ingest" \
     -F "files=@$(pwd)/test_doc.txt"
   ```

### Issue: "@ symbol not working"

**Problem:** zsh interpreting `@` symbol

**Solutions:**
1. Use single quotes around the entire `-F` value:
   ```bash
   curl -X POST "http://localhost:8000/agent/ingest" \
     -F 'files=@test_doc.txt'
   ```

2. Escape the `@`:
   ```bash
   curl -X POST "http://localhost:8000/agent/ingest" \
     -F "files=\@test_doc.txt"
   ```

### Issue: "curl: (26) Failed to open/read local file"

**Problem:** File doesn't exist or no read permissions

**Solutions:**
1. Check file exists:
   ```bash
   ls -la test_doc.txt
   ```

2. Check permissions:
   ```bash
   chmod 644 test_doc.txt
   ```

3. Use absolute path:
   ```bash
   curl -X POST "http://localhost:8000/agent/ingest" \
     -F "files=@$(realpath test_doc.txt)"
   ```

---

## Complete Working Examples

### Example 1: Upload from current directory
```bash
# Create test file
echo "Test content" > test.txt

# Upload it
curl -X POST "http://localhost:8000/agent/ingest" \
  -F "files=@test.txt"
```

### Example 2: Upload multiple files
```bash
# Create test files
echo "Content 1" > doc1.txt
echo "Content 2" > doc2.txt

# Upload both
curl -X POST "http://localhost:8000/agent/ingest" \
  -F "files=@doc1.txt" \
  -F "files=@doc2.txt"
```

### Example 3: Upload with verbose output (for debugging)
```bash
curl -v -X POST "http://localhost:8000/agent/ingest" \
  -F "files=@test_doc.txt"
```

### Example 4: Upload and see response
```bash
curl -X POST "http://localhost:8000/agent/ingest" \
  -F "files=@test_doc.txt" \
  | jq .
```

---

## Alternative: Using a Script

Create a helper script `upload.sh`:

```bash
#!/bin/zsh

# Upload files to agent
FILES=("$@")

if [ ${#FILES[@]} -eq 0 ]; then
    echo "Usage: $0 file1.txt file2.txt ..."
    exit 1
fi

CURL_CMD="curl -X POST 'http://localhost:8000/agent/ingest'"

for file in "${FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "Error: File not found: $file"
        exit 1
    fi
    CURL_CMD="$CURL_CMD -F \"files=@$file\""
done

eval $CURL_CMD
```

Make it executable and use:
```bash
chmod +x upload.sh
./upload.sh test_doc.txt test_doc2.txt
```

---

## Quick Test Command

Test if your server is running and the endpoint works:

```bash
# 1. Create a test file
echo "This is a test document" > test.txt

# 2. Upload it
curl -X POST "http://localhost:8000/agent/ingest" \
  -F "files=@test.txt"

# Expected response:
# {"status":"success","files_ingested":1}
```

---

## Notes for zsh Users

- Always quote file paths with spaces
- Use `$(pwd)` for relative paths if having issues
- Check file exists with `ls -la filename` before uploading
- Use `-v` flag for verbose output to debug issues
- Consider using absolute paths if relative paths don't work

