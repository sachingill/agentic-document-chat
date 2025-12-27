# Why Multiple ChromaDB Instances Exist

## Problem Overview

You have **100+ ChromaDB directories** (`ragdb_fresh_*`) because of an automatic fallback mechanism that creates new databases when corruption is detected.

---

## Root Cause

### The Fallback Mechanism

In `app/models/embeddings.py`, there's a **corruption detection and fallback system**:

```python
def _init_vector_db(*, base_dir: str | None = None, force_fresh: bool = False) -> Chroma:
    """
    Initialize Chroma with a persistent directory.
    
    We occasionally see older/incompatible SQLite metadata in ./ragdb (e.g. after upgrades),
    which can crash ingestion. To be robust, we fall back to a fresh directory WITHOUT
    deleting the original data.
    """
    base_dir = base_dir or os.getenv("RAGDB_DIR", "./ragdb")
    chosen_dir = _fresh_dir(base_dir) if force_fresh else base_dir
    
    try:
        db = Chroma(persist_directory=chosen_dir, collection_name="doc", embedding_function=EMBEDDINGS)
        _ = db._collection.count()  # Trigger initialization
        return db
    except (TypeError, Exception) as e:
        # If corruption detected, create fresh DB
        if is_corruption_error:
            fallback_dir = _fresh_dir(base_dir)  # Creates ragdb_fresh_<timestamp>
            db = Chroma(persist_directory=fallback_dir, ...)
            return db
```

### What Happens

1. **Corruption Detection**: When ChromaDB detects SQLite metadata corruption (e.g., `TypeError: object of type 'int' has no len()`)
2. **Fallback Creation**: Creates a new directory `ragdb_fresh_<timestamp>`
3. **No Cleanup**: Old databases are **never deleted** (by design, to preserve data)
4. **Accumulation**: Over time, this creates many `ragdb_fresh_*` directories

### Why So Many?

The fallback is triggered when:
- ChromaDB version upgrades cause schema incompatibilities
- SQLite metadata corruption occurs
- Development/testing causes frequent DB resets
- Ingestion errors trigger fallback during runtime

**Result**: Each corruption event creates a new DB, leading to 100+ directories.

---

## Current State

### Active Database

**Only ONE database is actually used** at runtime:
- The system initializes `VECTOR_DB` once at startup
- All queries/ingestion use this single instance
- Other directories are **orphaned** (not used)

### Which DB is Active?

The active DB is determined by:
1. **Startup**: First successful initialization
2. **Fallback**: If corruption detected, switches to `ragdb_fresh_<timestamp>`
3. **Runtime**: If ingestion fails, creates another fresh DB

**Check active DB:**
```python
from app.models.embeddings import VECTOR_DB
print(VECTOR_DB._persist_directory)  # Shows which DB is active
```

---

## Impact

### Storage

- **Disk Space**: Each DB directory can be 10-100MB+
- **100+ directories**: Potentially **1-10GB** of unused data
- **Waste**: Most directories are empty or duplicates

### Performance

- **No Performance Impact**: Only one DB is used
- **Startup Time**: Slight delay checking for corruption
- **Confusion**: Hard to know which DB is active

### Data Loss Risk

- **Orphaned Data**: Old databases may contain data not in active DB
- **No Migration**: Data isn't migrated between DBs
- **Silent Loss**: If fallback triggers, old data may be lost

---

## Solutions

### Option 1: Clean Up Old Databases (Recommended)

**Script to identify and clean up old databases:**

```python
#!/usr/bin/env python3
"""Clean up old ragdb_fresh_* directories, keeping only the active one."""

import os
import shutil
from pathlib import Path
from app.models.embeddings import VECTOR_DB

# Get active DB directory
active_dir = VECTOR_DB._persist_directory
print(f"Active DB: {active_dir}")

# Find all ragdb_fresh_* directories
project_root = Path(__file__).parent.parent
all_dbs = [d for d in project_root.iterdir() 
           if d.is_dir() and d.name.startswith("ragdb_fresh_")]

print(f"\nFound {len(all_dbs)} fresh DB directories")

# Keep active DB, delete others
deleted = 0
for db_dir in all_dbs:
    if str(db_dir) != active_dir:
        try:
            shutil.rmtree(db_dir)
            deleted += 1
            print(f"Deleted: {db_dir.name}")
        except Exception as e:
            print(f"Failed to delete {db_dir.name}: {e}")

print(f"\nDeleted {deleted} old databases")
print(f"Kept active DB: {active_dir}")
```

### Option 2: Use Single Database

**Modify `_init_vector_db` to reuse existing DB:**

```python
def _init_vector_db(*, base_dir: str | None = None, force_fresh: bool = False) -> Chroma:
    base_dir = base_dir or os.getenv("RAGDB_DIR", "./ragdb")
    
    # Always use base_dir, don't create fresh unless explicitly requested
    if force_fresh:
        chosen_dir = _fresh_dir(base_dir)
    else:
        chosen_dir = base_dir
    
    try:
        db = Chroma(persist_directory=chosen_dir, collection_name="doc", embedding_function=EMBEDDINGS)
        _ = db._collection.count()
        return db
    except Exception as e:
        # Only fallback if corruption is confirmed
        if is_corruption_error:
            # Try to repair or recreate base_dir instead of creating new
            logger.error("ChromaDB corruption detected. Recreating base directory...")
            if os.path.exists(base_dir):
                shutil.rmtree(base_dir)  # Remove corrupted DB
            db = Chroma(persist_directory=base_dir, collection_name="doc", embedding_function=EMBEDDINGS)
            return db
        raise
```

### Option 3: Environment Variable Control

**Use `RAGDB_DIR` to specify single DB:**

```bash
# Set environment variable to use single DB
export RAGDB_DIR="./ragdb_production"

# Or in .env file
RAGDB_DIR=./ragdb_production
```

### Option 4: Disable Fallback (Development Only)

**For development, disable automatic fallback:**

```python
def _init_vector_db(*, base_dir: str | None = None, force_fresh: bool = False) -> Chroma:
    base_dir = base_dir or os.getenv("RAGDB_DIR", "./ragdb")
    
    # In development, fail fast instead of creating new DBs
    if os.getenv("ENV") == "development":
        db = Chroma(persist_directory=base_dir, collection_name="doc", embedding_function=EMBEDDINGS)
        return db
    
    # Production: keep fallback logic
    # ... existing fallback code ...
```

---

## Recommended Action Plan

### Step 1: Identify Active DB

```bash
# Check which DB is currently active
python3 -c "from app.models.embeddings import VECTOR_DB; print(VECTOR_DB._persist_directory)"
```

### Step 2: Backup Active DB (Optional)

```bash
# Backup active database
ACTIVE_DB=$(python3 -c "from app.models.embeddings import VECTOR_DB; print(VECTOR_DB._persist_directory)")
cp -r "$ACTIVE_DB" "${ACTIVE_DB}_backup"
```

### Step 3: Clean Up Old Databases

```bash
# Run cleanup script (create script from Option 1 above)
python3 scripts/cleanup_old_chromadb.py
```

### Step 4: Consolidate to Single DB

```bash
# Set environment variable to use single DB
export RAGDB_DIR="./ragdb"

# Restart application
# System will use ./ragdb going forward
```

### Step 5: Update Code (Optional)

Modify `_init_vector_db` to:
- Reuse existing DB instead of creating new ones
- Only create fresh DB when explicitly requested
- Log fallback events for monitoring

---

## Prevention

### 1. Fix Root Cause

**Investigate why corruption occurs:**
- ChromaDB version compatibility issues?
- Concurrent access problems?
- Disk I/O errors?
- Memory issues?

### 2. Add Monitoring

```python
def _init_vector_db(...):
    try:
        db = Chroma(...)
        return db
    except Exception as e:
        # Log fallback events
        logger.warning("ChromaDB fallback triggered", extra={
            "error": str(e),
            "base_dir": base_dir,
            "fallback_dir": fallback_dir
        })
        # Send alert if fallback happens frequently
        if fallback_count > 5:
            send_alert("ChromaDB corruption detected multiple times")
```

### 3. Regular Maintenance

- **Cleanup script**: Run periodically to remove old DBs
- **Health checks**: Monitor DB health
- **Backup**: Backup active DB regularly

---

## Summary

**Why Multiple DBs Exist:**
- ✅ Automatic fallback mechanism creates new DBs on corruption
- ✅ No cleanup mechanism removes old DBs
- ✅ Development/testing triggers frequent fallbacks

**Current Impact:**
- ⚠️ 100+ unused directories consuming disk space
- ⚠️ Only one DB is actually used
- ⚠️ Potential data loss if fallback triggers

**Recommended Solution:**
1. ✅ Identify active DB
2. ✅ Clean up old databases
3. ✅ Consolidate to single DB
4. ✅ Fix root cause of corruption
5. ✅ Add monitoring and cleanup

**Quick Fix:**
```bash
# Clean up old DBs (keep active one)
python3 scripts/cleanup_old_chromadb.py

# Use single DB going forward
export RAGDB_DIR="./ragdb"
```

