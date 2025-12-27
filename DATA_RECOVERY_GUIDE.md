# Data Recovery Guide

## Overview

This guide explains how to recover and consolidate data from all ChromaDB instances into a single, safe database.

---

## Current Situation

- **147+ ChromaDB directories** exist (`ragdb` + `ragdb_fresh_*`)
- **Data is fragmented** across multiple databases
- **Only one DB is active** at any time
- **Data loss occurs** when fallback creates new empty DBs

---

## Recovery Process

### Step 1: Check Current Data Status

First, assess what data is recoverable:

```bash
# Check all databases for accessible data
python scripts/check_all_chromadb_data.py
```

This will show:
- Which databases are accessible
- Document count in each
- Which database is currently active
- Data loss assessment

### Step 2: Run Recovery Script

The recovery script will:
1. ✅ Check all databases for accessible data
2. ✅ Recover documents from all accessible databases
3. ✅ Deduplicate recovered documents
4. ✅ Create a single consolidated database
5. ✅ Switch system to use recovered database
6. ✅ Create backups before making changes

**Run recovery:**

```bash
# Activate virtual environment if needed
source venv/bin/activate

# Run recovery script
python scripts/recover_chromadb_data.py
```

**What it does:**

1. **Scans all DBs**: Checks all 147+ databases
2. **Recovers data**: Extracts documents from accessible DBs
3. **Deduplicates**: Removes duplicate documents
4. **Creates recovery DB**: `ragdb_recovered` with all recovered data
5. **Backs up**: Creates backups before making changes
6. **Switches to production**: Copies recovery DB to `ragdb` (production location)
7. **Verifies**: Confirms data integrity

### Step 3: Verify Recovery

After recovery, verify the data:

```bash
# Check document count in production DB
python3 -c "
from app.models.embeddings import VECTOR_DB
try:
    count = VECTOR_DB._collection.count()
    print(f'✅ Production DB has {count} documents')
except Exception as e:
    print(f'❌ Error: {e}')
"
```

### Step 4: Restart Application

Restart the application to use the recovered database:

```bash
# Stop current servers
./stop_local_dev.sh

# Start servers
./start_local_dev.sh
```

### Step 5: Test Data Access

Test that data is accessible:

```bash
# Test via API
curl -X POST http://localhost:8000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the three main authentication methods?",
    "session_id": "test"
  }'

# Or test via UI
# Open http://localhost:8501 and try a query
```

### Step 6: Clean Up Old Databases (Optional)

After verifying recovery works:

```bash
# Clean up old databases (keeps active one)
python scripts/cleanup_old_chromadb.py
```

**Warning**: Only run cleanup AFTER verifying recovery works!

---

## Recovery Script Details

### What Gets Recovered

- ✅ **All documents** from accessible databases
- ✅ **All metadata** (doc_id, category, tags, etc.)
- ✅ **All embeddings** (recreated during ingestion)

### What Gets Deduplicated

- ✅ Documents with same `chunk_id`
- ✅ Documents with identical content
- ✅ Prevents duplicate entries

### Backup Strategy

The script creates backups:
- `ragdb_backup_<timestamp>` - Backup of current production DB
- `ragdb_recovered_backup_<timestamp>` - Backup of recovery DB if it exists

**Backups are kept** so you can restore if needed.

---

## Troubleshooting

### Issue: "No accessible databases found"

**Cause**: All databases are corrupted

**Solution**:
1. Check if any DB files exist: `ls -la ragdb*/chroma.sqlite3`
2. Try manual recovery from SQLite files
3. Re-ingest critical documents manually

### Issue: "Recovery DB creation failed"

**Cause**: Disk space or permissions issue

**Solution**:
1. Check disk space: `df -h .`
2. Check permissions: `ls -la ragdb*`
3. Run with appropriate permissions

### Issue: "Document count mismatch"

**Cause**: Some documents may have failed to ingest

**Solution**:
1. Check recovery logs for errors
2. Re-run recovery script (it will skip duplicates)
3. Manually ingest any missing documents

### Issue: "Application still using old DB"

**Cause**: Application needs restart

**Solution**:
1. Stop application: `./stop_local_dev.sh`
2. Verify `ragdb` directory has recovered data
3. Restart application: `./start_local_dev.sh`

---

## Prevention: Fix Fallback Mechanism

After recovery, fix the fallback mechanism to prevent future data loss:

### Option 1: Add Data Recovery to Fallback

Modify `app/models/embeddings.py` to recover data during fallback:

```python
def _init_vector_db(*, base_dir: str | None = None, force_fresh: bool = False) -> Chroma:
    base_dir = base_dir or os.getenv("RAGDB_DIR", "./ragdb")
    
    try:
        db = Chroma(persist_directory=base_dir, ...)
        _ = db._collection.count()
        return db
    except Exception as e:
        if is_corruption_error:
            logger.warning("Corruption detected, attempting data recovery...")
            
            # Try to recover data
            try:
                old_db = Chroma(persist_directory=base_dir, ...)
                all_data = old_db.get()
                documents = all_data.get("documents", [])
                
                if documents:
                    # Create new DB and re-ingest
                    fallback_dir = _fresh_dir(base_dir)
                    new_db = Chroma(persist_directory=fallback_dir, ...)
                    new_db.add_texts(
                        documents,
                        ids=all_data.get("ids"),
                        metadatas=all_data.get("metadatas")
                    )
                    logger.info(f"Data recovered to {fallback_dir}")
                    return new_db
            except Exception as recovery_error:
                logger.error(f"Data recovery failed: {recovery_error}")
            
            # If recovery fails, create empty DB
            fallback_dir = _fresh_dir(base_dir)
            return Chroma(persist_directory=fallback_dir, ...)
        raise
```

### Option 2: Use Single Database (No Fallback)

Modify to always use same DB:

```python
def _init_vector_db(*, base_dir: str | None = None, force_fresh: bool = False) -> Chroma:
    base_dir = base_dir or os.getenv("RAGDB_DIR", "./ragdb")
    
    # Always use base_dir, never create fresh unless explicitly requested
    if force_fresh:
        chosen_dir = _fresh_dir(base_dir)
    else:
        chosen_dir = base_dir
    
    try:
        db = Chroma(persist_directory=chosen_dir, ...)
        _ = db._collection.count()
        return db
    except Exception as e:
        # Log error but don't create new DB
        logger.error(f"ChromaDB error: {e}")
        raise  # Fail fast instead of creating new DB
```

---

## Summary

### Recovery Steps

1. ✅ **Check status**: `python scripts/check_all_chromadb_data.py`
2. ✅ **Run recovery**: `python scripts/recover_chromadb_data.py`
3. ✅ **Verify**: Check document count
4. ✅ **Restart**: Restart application
5. ✅ **Test**: Verify data access
6. ✅ **Cleanup**: Remove old DBs (optional)

### Expected Results

- ✅ **Single consolidated database** (`ragdb`)
- ✅ **All recoverable data** preserved
- ✅ **No duplicates** in final database
- ✅ **Backups created** for safety
- ✅ **System ready** to use recovered data

### Next Steps After Recovery

1. ✅ Fix fallback mechanism to prevent future loss
2. ✅ Set up regular backups
3. ✅ Monitor database health
4. ✅ Clean up old databases

---

## Quick Reference

```bash
# Check data status
python scripts/check_all_chromadb_data.py

# Recover data
python scripts/recover_chromadb_data.py

# Verify recovery
python3 -c "from app.models.embeddings import VECTOR_DB; print(VECTOR_DB._collection.count())"

# Restart application
./stop_local_dev.sh && ./start_local_dev.sh

# Clean up old DBs (after verification)
python scripts/cleanup_old_chromadb.py
```

---

## Support

If recovery fails:
1. Check error messages in recovery script output
2. Review backup directories (`ragdb_backup_*`)
3. Try manual recovery from specific databases
4. Re-ingest critical documents if needed

