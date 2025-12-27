# Data Loss Analysis: ChromaDB Fallback Mechanism

## Critical Finding: ⚠️ **YES, DATA IS LOST**

When the fallback mechanism creates a new ChromaDB, **existing data is NOT migrated**. The old corrupted database is abandoned, and the new database starts empty.

---

## How Fallback Works (Current Implementation)

### Step-by-Step Process

1. **Corruption Detected**
   ```python
   # System tries to use existing DB
   db = Chroma(persist_directory="./ragdb", ...)
   _ = db._collection.count()  # ❌ Fails with TypeError
   ```

2. **Fallback Triggered**
   ```python
   # Creates NEW empty database
   fallback_dir = "ragdb_fresh_<timestamp>"
   db = Chroma(persist_directory=fallback_dir, ...)  # ✅ New empty DB
   ```

3. **Data Status**
   - ❌ **Old DB**: Abandoned, data still there but not accessible
   - ✅ **New DB**: Empty, ready for new ingestion
   - ⚠️ **Data Loss**: All previous documents are lost from active system

### Code Analysis

Looking at `app/models/embeddings.py`:

```python
def _init_vector_db(*, base_dir: str | None = None, force_fresh: bool = False) -> Chroma:
    base_dir = base_dir or os.getenv("RAGDB_DIR", "./ragdb")
    chosen_dir = _fresh_dir(base_dir) if force_fresh else base_dir
    
    try:
        db = Chroma(persist_directory=chosen_dir, ...)
        _ = db._collection.count()
        return db
    except Exception as e:
        if is_corruption_error:
            # ⚠️ Creates NEW empty DB - NO DATA MIGRATION
            fallback_dir = _fresh_dir(base_dir)
            db = Chroma(persist_directory=fallback_dir, ...)
            return db  # Returns empty DB
```

**Key Point**: There's **NO code** to:
- Copy documents from old DB to new DB
- Migrate embeddings
- Preserve metadata
- Transfer any data

---

## Data Loss Scenarios

### Scenario 1: Startup Corruption

**What Happens:**
1. System starts, tries to load `./ragdb`
2. Corruption detected (e.g., SQLite metadata error)
3. Fallback creates `ragdb_fresh_<timestamp>`
4. System uses empty new DB

**Data Loss:**
- ✅ Old DB still exists on disk (not deleted)
- ❌ Old DB is **not accessible** (corrupted)
- ❌ New DB is **empty**
- ⚠️ **All data lost from active system**

### Scenario 2: Runtime Ingestion Error

**What Happens:**
1. Ingestion tries to add documents to active DB
2. Corruption error occurs during `add_documents()`
3. System creates new DB and retries ingestion
4. Only **new documents** are ingested

**Data Loss:**
- ✅ Previously ingested documents still in old DB
- ❌ Old DB is **not accessible** (corrupted)
- ✅ New documents successfully ingested
- ⚠️ **Previous data lost**, only new data available

### Scenario 3: Multiple Fallbacks

**What Happens:**
1. First fallback: `ragdb_fresh_001` created
2. Second fallback: `ragdb_fresh_002` created
3. Each fallback abandons previous DB

**Data Loss:**
- ❌ Each fallback loses data from previous DB
- ⚠️ **Cumulative data loss** across multiple fallbacks

---

## Current Data Status

### Where Your Data Might Be

1. **Main `ragdb` Directory**
   - May contain data if corruption hasn't occurred yet
   - May be corrupted and inaccessible
   - Status: Unknown without checking

2. **`ragdb_fresh_*` Directories**
   - Each contains data from when it was active
   - Most recent `ragdb_fresh_*` likely has most recent data
   - Older ones may have partial data

3. **Active Database**
   - Only ONE is currently active
   - Contains only data ingested AFTER it became active
   - May be empty if fallback happened early

### How to Check

```python
from app.models.embeddings import VECTOR_DB

# Check active DB
active_path = VECTOR_DB._persist_directory
print(f"Active DB: {active_path}")

# Count documents in active DB
try:
    count = VECTOR_DB._collection.count()
    print(f"Documents in active DB: {count}")
except Exception as e:
    print(f"Error accessing active DB: {e}")
```

---

## Data Recovery Options

### Option 1: Recover from Old DBs (If Not Corrupted)

**If old DBs are accessible:**

```python
from langchain_chroma import Chroma
from app.models.embeddings import EMBEDDINGS

# Try to access old DB
old_db_path = "./ragdb"  # or specific ragdb_fresh_*
try:
    old_db = Chroma(persist_directory=old_db_path, 
                    collection_name="doc", 
                    embedding_function=EMBEDDINGS)
    count = old_db._collection.count()
    print(f"Found {count} documents in {old_db_path}")
    
    # Retrieve all documents
    retriever = old_db.as_retriever(search_kwargs={"k": count})
    docs = retriever.get_relevant_documents("")  # Empty query gets all
    
    # Re-ingest into active DB
    from app.models.embeddings import VECTOR_DB
    VECTOR_DB.add_documents([d.page_content for d in docs], 
                            metadata=[d.metadata for d in docs])
    print("Data recovered!")
except Exception as e:
    print(f"Cannot recover from {old_db_path}: {e}")
```

### Option 2: Manual Data Export/Import

**Export from old DB:**
```python
# Export documents from old DB
old_db = Chroma(persist_directory="./ragdb", ...)
all_docs = old_db.get()  # Get all documents

# Save to JSON
import json
with open("recovered_data.json", "w") as f:
    json.dump({
        "documents": all_docs["documents"],
        "metadatas": all_docs["metadatas"],
        "ids": all_docs["ids"]
    }, f)
```

**Import to new DB:**
```python
# Load and re-ingest
with open("recovered_data.json", "r") as f:
    data = json.load(f)

from app.models.embeddings import ingest_documents
ingest_documents(data["documents"], metadata=data["metadatas"])
```

### Option 3: Check All DBs and Consolidate

**Script to find data in all DBs:**

```python
from pathlib import Path
from langchain_chroma import Chroma
from app.models.embeddings import EMBEDDINGS

all_dbs = [Path("ragdb")] + list(Path(".").glob("ragdb_fresh_*"))

for db_path in all_dbs:
    try:
        db = Chroma(persist_directory=str(db_path), 
                    collection_name="doc", 
                    embedding_function=EMBEDDINGS)
        count = db._collection.count()
        print(f"✅ {db_path.name}: {count} documents")
    except Exception as e:
        print(f"❌ {db_path.name}: Cannot access ({type(e).__name__})")
```

---

## Prevention: Fix the Fallback Mechanism

### Improved Fallback with Data Recovery

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
            
            # Try to recover data before creating new DB
            try:
                old_db = Chroma(persist_directory=base_dir, ...)
                # Try to get documents (may work even if count() fails)
                all_data = old_db.get()
                documents = all_data.get("documents", [])
                
                if documents:
                    logger.info(f"Recovered {len(documents)} documents from corrupted DB")
                    # Create new DB
                    fallback_dir = _fresh_dir(base_dir)
                    new_db = Chroma(persist_directory=fallback_dir, ...)
                    # Re-ingest recovered data
                    new_db.add_documents(
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
            logger.warning(f"Creating empty fallback DB at {fallback_dir}")
            return Chroma(persist_directory=fallback_dir, ...)
        raise
```

### Better: Repair Instead of Replace

```python
def _init_vector_db(*, base_dir: str | None = None, force_fresh: bool = False) -> Chroma:
    base_dir = base_dir or os.getenv("RAGDB_DIR", "./ragdb")
    
    try:
        db = Chroma(persist_directory=base_dir, ...)
        _ = db._collection.count()
        return db
    except Exception as e:
        if is_corruption_error:
            logger.warning("Corruption detected, attempting repair...")
            
            # Try to repair by recreating metadata
            try:
                # Backup corrupted DB
                backup_dir = f"{base_dir}_corrupted_backup"
                shutil.copytree(base_dir, backup_dir)
                
                # Try to extract data before repair
                # ... recovery logic ...
                
                # Remove corrupted DB and recreate
                shutil.rmtree(base_dir)
                db = Chroma(persist_directory=base_dir, ...)
                
                # Re-ingest recovered data
                # ... re-ingestion logic ...
                
                logger.info("DB repaired successfully")
                return db
            except Exception as repair_error:
                logger.error(f"Repair failed: {repair_error}")
                # Fall back to new DB
                return _create_fresh_db(base_dir)
        raise
```

---

## Immediate Action Plan

### Step 1: Assess Data Loss

```bash
# Check active DB document count
python3 -c "
from app.models.embeddings import VECTOR_DB
try:
    count = VECTOR_DB._collection.count()
    print(f'Active DB has {count} documents')
except Exception as e:
    print(f'Error: {e}')
"
```

### Step 2: Check All DBs for Data

```bash
# Run recovery check script
python3 scripts/check_all_chromadb_data.py
```

### Step 3: Recover Data (If Possible)

```bash
# Try to recover from old DBs
python3 scripts/recover_chromadb_data.py
```

### Step 4: Re-ingest Critical Data

If recovery fails, you'll need to:
1. Identify critical documents
2. Re-ingest them manually
3. Use training dataset to rebuild knowledge base

---

## Summary

### Current Situation

- ⚠️ **Data Loss Confirmed**: Fallback mechanism does NOT migrate data
- ⚠️ **Old DBs Abandoned**: Corrupted DBs remain on disk but unused
- ⚠️ **New DBs Empty**: Each fallback starts with empty database
- ⚠️ **Cumulative Loss**: Multiple fallbacks = multiple data losses

### Data Status

- **Active DB**: Contains only data ingested after it became active
- **Old DBs**: May contain data, but inaccessible if corrupted
- **Recovery**: Possible if old DBs are not fully corrupted

### Recommendations

1. ✅ **Immediate**: Check active DB document count
2. ✅ **Immediate**: Attempt data recovery from old DBs
3. ✅ **Short-term**: Fix fallback mechanism to preserve data
4. ✅ **Long-term**: Prevent corruption root cause

### Next Steps

1. Run data recovery script to check all DBs
2. Consolidate data into single active DB
3. Fix fallback mechanism to prevent future loss
4. Implement regular backups

**Bottom Line**: Yes, data is lost when fallback occurs. However, old DBs may still be recoverable if corruption is limited. Check immediately!

