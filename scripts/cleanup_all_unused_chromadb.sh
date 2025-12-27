#!/bin/bash
# Clean up all unused ChromaDB directories
# Keeps only the active database

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "============================================================"
echo "ChromaDB Cleanup - Remove Unused Directories"
echo "============================================================"
echo ""

# Check if virtual environment exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Get active database
echo "Step 1: Identifying active database..."
echo "============================================================"

ACTIVE_DB=""
ACTIVE_NAME=""

python3 << 'PYTHON_SCRIPT'
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))

try:
    from app.models.embeddings import VECTOR_DB
    active_path = VECTOR_DB._persist_directory
    active_name = Path(active_path).name
    print(f"✅ Active DB: {active_name}")
    print(f"   Full path: {active_path}")
    # Write to file for bash to read
    with open("/tmp/active_db.txt", "w") as f:
        f.write(f"{active_name}\n{active_path}\n")
except Exception as e:
    print(f"⚠️  Could not determine active DB: {e}")
    print("   Will proceed with manual selection")
PYTHON_SCRIPT

if [ -f "/tmp/active_db.txt" ]; then
    ACTIVE_NAME=$(head -n 1 /tmp/active_db.txt)
    ACTIVE_DB=$(tail -n 1 /tmp/active_db.txt)
    rm /tmp/active_db.txt
    echo ""
    echo "Active database identified: $ACTIVE_NAME"
else
    echo ""
    echo "⚠️  Could not automatically identify active database"
    echo "   Please specify which database to keep:"
    echo ""
    ls -d ragdb* 2>/dev/null | head -10
    echo ""
    read -p "Enter database name to keep (or 'cancel' to abort): " ACTIVE_NAME
    if [ "$ACTIVE_NAME" = "cancel" ]; then
        echo "❌ Cleanup cancelled"
        exit 1
    fi
fi

# Find all ChromaDB directories
echo ""
echo "Step 2: Finding all ChromaDB directories..."
echo "============================================================"

ALL_DBS=($(ls -d ragdb* 2>/dev/null | sort))
TOTAL_COUNT=${#ALL_DBS[@]}

if [ $TOTAL_COUNT -eq 0 ]; then
    echo "❌ No ChromaDB directories found"
    exit 1
fi

echo "Found $TOTAL_COUNT ChromaDB directories:"
for db in "${ALL_DBS[@]}"; do
    if [ "$db" = "$ACTIVE_NAME" ]; then
        echo "  ✅ KEEP:    $db [ACTIVE]"
    else
        echo "  🗑️  DELETE:  $db"
    fi
done

# Calculate total size
echo ""
echo "Step 3: Calculating disk space to free..."
echo "============================================================"

TOTAL_SIZE=0
for db in "${ALL_DBS[@]}"; do
    if [ "$db" != "$ACTIVE_NAME" ] && [ -d "$db" ]; then
        SIZE=$(du -sm "$db" 2>/dev/null | cut -f1 || echo "0")
        TOTAL_SIZE=$((TOTAL_SIZE + SIZE))
    fi
done

echo "  • Directories to delete: $((TOTAL_COUNT - 1))"
echo "  • Disk space to free: ${TOTAL_SIZE} MB (~$((TOTAL_SIZE / 1024)) GB)"

# Confirmation
echo ""
echo "============================================================"
echo "⚠️  WARNING: This will permanently delete unused databases!"
echo "============================================================"
echo ""
echo "Will keep:    $ACTIVE_NAME"
echo "Will delete:  $((TOTAL_COUNT - 1)) directories"
echo "Will free:    ${TOTAL_SIZE} MB"
echo ""
read -p "Are you sure you want to proceed? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ] && [ "$CONFIRM" != "y" ]; then
    echo "❌ Cleanup cancelled"
    exit 0
fi

# Create backup of active DB (just in case)
echo ""
echo "Step 4: Creating backup of active database..."
echo "============================================================"

BACKUP_NAME="${ACTIVE_NAME}_backup_$(date +%Y%m%d_%H%M%S)"
if [ -d "$ACTIVE_NAME" ]; then
    cp -r "$ACTIVE_NAME" "$BACKUP_NAME" && echo "✅ Backup created: $BACKUP_NAME" || echo "⚠️  Backup failed (continuing anyway)"
else
    echo "⚠️  Active database directory not found, skipping backup"
fi

# Delete unused directories
echo ""
echo "Step 5: Deleting unused directories..."
echo "============================================================"

DELETED=0
FAILED=0

for db in "${ALL_DBS[@]}"; do
    if [ "$db" != "$ACTIVE_NAME" ] && [ -d "$db" ]; then
        echo -n "  Deleting $db... "
        if rm -rf "$db" 2>/dev/null; then
            echo "✅"
            DELETED=$((DELETED + 1))
        else
            echo "❌ Failed"
            FAILED=$((FAILED + 1))
        fi
    fi
done

# Summary
echo ""
echo "============================================================"
echo "Cleanup Complete!"
echo "============================================================"
echo "  • Total directories found: $TOTAL_COUNT"
echo "  • Kept (active): 1 ($ACTIVE_NAME)"
echo "  • Deleted: $DELETED"
if [ $FAILED -gt 0 ]; then
    echo "  • Failed: $FAILED"
fi
echo "  • Disk space freed: ${TOTAL_SIZE} MB"
echo ""
echo "✅ Cleanup completed successfully!"
echo ""
echo "Remaining directories:"
ls -d ragdb* 2>/dev/null | wc -l | xargs echo "  Total:"

