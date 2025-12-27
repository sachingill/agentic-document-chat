#!/bin/bash
# Quick cleanup - removes all ragdb_fresh_* directories
# Keeps main ragdb directory

set -e

cd "$(dirname "$0")/.."

echo "============================================================"
echo "Quick Cleanup - Remove ragdb_fresh_* directories"
echo "============================================================"
echo ""

# Count directories
FRESH_COUNT=$(ls -d ragdb_fresh_* 2>/dev/null | wc -l | tr -d ' ')
MAIN_EXISTS=$(test -d ragdb && echo "yes" || echo "no")

echo "Found:"
echo "  • ragdb_fresh_* directories: $FRESH_COUNT"
echo "  • Main ragdb directory: $MAIN_EXISTS"
echo ""

if [ "$FRESH_COUNT" -eq 0 ]; then
    echo "✅ No ragdb_fresh_* directories to clean"
    exit 0
fi

# Calculate size
echo "Calculating disk space..."
TOTAL_SIZE=$(du -sm ragdb_fresh_* 2>/dev/null | awk '{sum+=$1} END {print sum}' || echo "0")
echo "  • Total size: ${TOTAL_SIZE} MB (~$((TOTAL_SIZE / 1024)) GB)"
echo ""

# Confirmation
echo "⚠️  This will delete all $FRESH_COUNT ragdb_fresh_* directories"
echo "   Main 'ragdb' directory will be preserved"
echo ""
read -p "Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ] && [ "$CONFIRM" != "y" ]; then
    echo "❌ Cleanup cancelled"
    exit 0
fi

# Delete
echo ""
echo "Deleting directories..."
DELETED=0
FAILED=0

for dir in ragdb_fresh_*; do
    if [ -d "$dir" ]; then
        echo -n "  Deleting $dir... "
        if rm -rf "$dir" 2>/dev/null; then
            echo "✅"
            DELETED=$((DELETED + 1))
        else
            echo "❌"
            FAILED=$((FAILED + 1))
        fi
    fi
done

# Summary
echo ""
echo "============================================================"
echo "Cleanup Complete!"
echo "============================================================"
echo "  • Deleted: $DELETED directories"
if [ $FAILED -gt 0 ]; then
    echo "  • Failed: $FAILED directories"
fi
echo "  • Freed: ${TOTAL_SIZE} MB"
echo ""
echo "Remaining directories:"
ls -d ragdb* 2>/dev/null | wc -l | xargs echo "  Total:"

