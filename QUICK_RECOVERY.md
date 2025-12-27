# Quick Data Recovery Guide

## 🚨 Immediate Action Required

Your data is fragmented across 147+ ChromaDB directories. Follow these steps to recover and consolidate it.

---

## Quick Recovery (Recommended)

### Option 1: Automated Recovery Script

```bash
# Run the safe recovery script (handles everything)
./scripts/safe_recovery.sh
```

This will:
- ✅ Check all databases
- ✅ Create backups
- ✅ Recover all accessible data
- ✅ Consolidate into single database
- ✅ Verify recovery

### Option 2: Manual Recovery Steps

If the automated script doesn't work, follow these steps:

```bash
# 1. Activate virtual environment
source venv/bin/activate  # or: source .venv/bin/activate

# 2. Check current data status
python scripts/check_all_chromadb_data.py

# 3. Create backup (IMPORTANT!)
cp -r ragdb ragdb_backup_$(date +%Y%m%d_%H%M%S)

# 4. Run recovery
python scripts/recover_chromadb_data.py

# 5. Verify recovery
python3 -c "from app.models.embeddings import VECTOR_DB; print(f'Documents: {VECTOR_DB._collection.count()}')"

# 6. Restart application
./stop_local_dev.sh
./start_local_dev.sh
```

---

## What Gets Recovered

✅ **All documents** from accessible databases  
✅ **All metadata** (doc_id, category, tags, etc.)  
✅ **Deduplicated** (no duplicates)  
✅ **Consolidated** into single `ragdb` directory  

---

## Safety Features

- ✅ **Backups created** before any changes
- ✅ **No data deletion** - old DBs preserved
- ✅ **Verification** after recovery
- ✅ **Rollback possible** using backups

---

## After Recovery

1. ✅ **Verify**: Test queries via API/UI
2. ✅ **Monitor**: Check application logs
3. ✅ **Cleanup**: Remove old DBs (optional)
   ```bash
   python scripts/cleanup_old_chromadb.py
   ```

---

## Troubleshooting

### "ModuleNotFoundError"
```bash
# Make sure virtual environment is activated
source venv/bin/activate
pip install -r requirements.txt
```

### "Permission denied"
```bash
# Check permissions
ls -la ragdb*
# Fix if needed
chmod -R u+w ragdb*
```

### "Disk space"
```bash
# Check disk space
df -h .
# Free up space if needed
```

---

## Need Help?

See detailed guide: `DATA_RECOVERY_GUIDE.md`

---

## Summary

**Run this command:**
```bash
./scripts/safe_recovery.sh
```

**Then restart your application:**
```bash
./stop_local_dev.sh && ./start_local_dev.sh
```

**Your data will be safe and consolidated!** ✅

