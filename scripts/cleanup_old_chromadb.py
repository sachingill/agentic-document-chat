#!/usr/bin/env python3
"""
Clean up old ragdb_fresh_* directories, keeping only the active one.

This script:
1. Identifies the active ChromaDB directory
2. Finds all ragdb_fresh_* directories
3. Deletes old ones, keeping only the active DB
"""

import os
import shutil
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from app.models.embeddings import VECTOR_DB
except ImportError as e:
    print(f"❌ Error importing VECTOR_DB: {e}")
    print("Make sure you're running from the project root and dependencies are installed.")
    sys.exit(1)


def get_active_db_path():
    """Get the path of the currently active ChromaDB."""
    try:
        active_path = VECTOR_DB._persist_directory
        return Path(active_path).resolve()
    except Exception as e:
        print(f"❌ Error getting active DB path: {e}")
        return None


def find_all_fresh_dbs(project_root: Path):
    """Find all ragdb_fresh_* directories."""
    fresh_dbs = []
    for item in project_root.iterdir():
        if item.is_dir() and item.name.startswith("ragdb_fresh_"):
            fresh_dbs.append(item.resolve())
    return sorted(fresh_dbs)


def get_db_size(db_path: Path):
    """Get size of database directory in MB."""
    try:
        total_size = sum(
            f.stat().st_size for f in db_path.rglob('*') if f.is_file()
        )
        return total_size / (1024 * 1024)  # Convert to MB
    except Exception:
        return 0


def main():
    print("=" * 60)
    print("ChromaDB Cleanup Script")
    print("=" * 60)
    
    # Get active DB
    active_db = get_active_db_path()
    if not active_db:
        print("❌ Could not determine active database")
        return 1
    
    print(f"\n✅ Active DB: {active_db}")
    
    # Find all fresh DBs
    fresh_dbs = find_all_fresh_dbs(project_root)
    
    if not fresh_dbs:
        print("\n✅ No ragdb_fresh_* directories found. Nothing to clean up.")
        return 0
    
    print(f"\n📊 Found {len(fresh_dbs)} ragdb_fresh_* directories")
    
    # Show summary
    total_size = 0
    to_delete = []
    to_keep = []
    
    for db_path in fresh_dbs:
        size_mb = get_db_size(db_path)
        total_size += size_mb
        
        if db_path == active_db:
            to_keep.append((db_path, size_mb))
            print(f"  ✅ KEEP: {db_path.name} ({size_mb:.2f} MB) [ACTIVE]")
        else:
            to_delete.append((db_path, size_mb))
            print(f"  🗑️  DELETE: {db_path.name} ({size_mb:.2f} MB)")
    
    print(f"\n📊 Summary:")
    print(f"  • Total directories: {len(fresh_dbs)}")
    print(f"  • To keep: {len(to_keep)}")
    print(f"  • To delete: {len(to_delete)}")
    print(f"  • Total size: {total_size:.2f} MB")
    
    if not to_delete:
        print("\n✅ Nothing to delete. All directories are in use or already cleaned.")
        return 0
    
    # Confirm deletion
    print(f"\n⚠️  About to delete {len(to_delete)} directories")
    response = input("Continue? (yes/no): ").strip().lower()
    
    if response not in ["yes", "y"]:
        print("❌ Cancelled")
        return 0
    
    # Delete old DBs
    deleted_count = 0
    deleted_size = 0
    failed = []
    
    print("\n🗑️  Deleting old databases...")
    for db_path, size_mb in to_delete:
        try:
            shutil.rmtree(db_path)
            deleted_count += 1
            deleted_size += size_mb
            print(f"  ✅ Deleted: {db_path.name}")
        except Exception as e:
            failed.append((db_path.name, str(e)))
            print(f"  ❌ Failed to delete {db_path.name}: {e}")
    
    # Summary
    print(f"\n✅ Cleanup complete!")
    print(f"  • Deleted: {deleted_count} directories")
    print(f"  • Freed: {deleted_size:.2f} MB")
    
    if failed:
        print(f"\n⚠️  Failed to delete {len(failed)} directories:")
        for name, error in failed:
            print(f"  • {name}: {error}")
    
    if to_keep:
        print(f"\n✅ Kept active DB: {to_keep[0][0].name}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

