#!/bin/bash
# Safe Data Recovery Script
# This script ensures data is recovered and safe before making any changes

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "============================================================"
echo "ChromaDB Data Recovery - Safe Mode"
echo "============================================================"
echo ""

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "✅ Virtual environment found"
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "✅ Virtual environment found (.venv)"
    source .venv/bin/activate
else
    echo "⚠️  No virtual environment found"
    echo "   Please activate your Python environment manually"
    echo "   Then run: python scripts/recover_chromadb_data.py"
    exit 1
fi

# Step 1: Check current data status
echo ""
echo "Step 1: Checking current data status..."
echo "============================================================"
python scripts/check_all_chromadb_data.py || {
    echo "⚠️  Status check failed, but continuing..."
}

# Step 2: Create backup of current production DB
echo ""
echo "Step 2: Creating backup of current production DB..."
echo "============================================================"
if [ -d "ragdb" ]; then
    BACKUP_NAME="ragdb_backup_$(date +%Y%m%d_%H%M%S)"
    echo "📦 Creating backup: $BACKUP_NAME"
    cp -r ragdb "$BACKUP_NAME" && echo "✅ Backup created: $BACKUP_NAME" || echo "⚠️  Backup failed"
else
    echo "ℹ️  No existing ragdb directory to backup"
fi

# Step 3: Run recovery
echo ""
echo "Step 3: Running data recovery..."
echo "============================================================"
python scripts/recover_chromadb_data.py

RECOVERY_EXIT_CODE=$?

if [ $RECOVERY_EXIT_CODE -eq 0 ]; then
    echo ""
    echo "============================================================"
    echo "✅ Recovery completed successfully!"
    echo "============================================================"
    echo ""
    echo "Next steps:"
    echo "  1. Verify data: python3 -c \"from app.models.embeddings import VECTOR_DB; print(f'Documents: {VECTOR_DB._collection.count()}')\""
    echo "  2. Restart application: ./stop_local_dev.sh && ./start_local_dev.sh"
    echo "  3. Test queries via API or UI"
    echo "  4. (Optional) Clean up old DBs: python scripts/cleanup_old_chromadb.py"
    echo ""
else
    echo ""
    echo "============================================================"
    echo "❌ Recovery failed with exit code: $RECOVERY_EXIT_CODE"
    echo "============================================================"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check error messages above"
    echo "  2. Verify backups were created"
    echo "  3. Check disk space: df -h ."
    echo "  4. Review DATA_RECOVERY_GUIDE.md for details"
    echo ""
    exit $RECOVERY_EXIT_CODE
fi

