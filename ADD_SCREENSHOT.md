# How to Add UI Screenshot

## Steps to Add the Screenshot

1. **Save your screenshot** as `ui_screenshot.png` in the project root directory:
   ```
   /Users/sachin/nltk_data/api/ui_screenshot.png
   ```

2. **Verify the file exists:**
   ```bash
   ls -la ui_screenshot.png
   ```

3. **Add to git:**
   ```bash
   git add ui_screenshot.png
   git commit -m "Add UI screenshot"
   git push
   ```

## Screenshot Requirements

- **Filename**: `ui_screenshot.png`
- **Location**: Root directory (same level as `ui.py`, `README.md`)
- **Format**: PNG (recommended) or JPG
- **Size**: Recommended max 1920x1080 for good display

## What the Screenshot Shows

The screenshot should display:
- Left sidebar with workflow selection (Structured RAG / Agentic RAG)
- Main chat area with conversation history
- User messages in purple bubbles
- Assistant responses with workflow badges and guardrail status
- API status indicators

## Documentation References

The screenshot is referenced in:
- `README.md` - Main project README
- `UI_README.md` - UI-specific documentation

Both files use: `![RAG Chat UI](ui_screenshot.png)`

