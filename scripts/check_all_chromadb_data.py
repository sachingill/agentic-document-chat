#!/usr/bin/env python3
"""
Check all ChromaDB directories for data and assess data loss.

This script:
1. Checks main ragdb directory
2. Checks all ragdb_fresh_* directories
3. Reports document counts and accessibility
4. Identifies which DBs have recoverable data
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_chroma import Chroma
except ImportError:
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_community.vectorstores import Chroma

EMBEDDINGS = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")


def check_db(db_path: Path) -> Tuple[bool, int, str]:
    """
    Check if a ChromaDB directory is accessible and count documents.
    
    Returns:
        (is_accessible, document_count, error_message)
    """
    try:
        db = Chroma(
            persist_directory=str(db_path),
            collection_name="doc",
            embedding_function=EMBEDDINGS
        )
        count = db._collection.count()
        return True, count, ""
    except Exception as e:
        return False, 0, str(e)


def get_db_size(db_path: Path) -> float:
    """Get size of database directory in MB."""
    try:
        total_size = sum(
            f.stat().st_size for f in db_path.rglob('*') if f.is_file()
        )
        return total_size / (1024 * 1024)  # Convert to MB
    except Exception:
        return 0


def find_all_dbs(project_root: Path) -> List[Path]:
    """Find all ChromaDB directories."""
    dbs = []
    
    # Main ragdb
    main_db = project_root / "ragdb"
    if main_db.exists():
        dbs.append(main_db)
    
    # All ragdb_fresh_* directories
    fresh_dbs = sorted(project_root.glob("ragdb_fresh_*"))
    dbs.extend(fresh_dbs)
    
    return dbs


def main():
    print("=" * 70)
    print("ChromaDB Data Loss Assessment")
    print("=" * 70)
    
    # Find all DBs
    all_dbs = find_all_dbs(project_root)
    
    if not all_dbs:
        print("\n❌ No ChromaDB directories found")
        return 1
    
    print(f"\n📊 Found {len(all_dbs)} ChromaDB directories")
    print("\nChecking accessibility and document counts...\n")
    
    # Check each DB
    results: List[Dict] = []
    total_documents = 0
    accessible_count = 0
    
    for db_path in all_dbs:
        is_accessible, doc_count, error = check_db(db_path)
        size_mb = get_db_size(db_path)
        
        status = "✅ ACCESSIBLE" if is_accessible else "❌ INACCESSIBLE"
        doc_info = f"{doc_count} documents" if is_accessible else f"Error: {error[:50]}"
        
        print(f"{status:20} | {db_path.name:40} | {doc_info:30} | {size_mb:6.2f} MB")
        
        results.append({
            "path": str(db_path),
            "name": db_path.name,
            "accessible": is_accessible,
            "document_count": doc_count,
            "size_mb": size_mb,
            "error": error
        })
        
        if is_accessible:
            accessible_count += 1
            total_documents += doc_count
    
    # Summary
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"Total DBs checked: {len(all_dbs)}")
    print(f"Accessible DBs: {accessible_count}")
    print(f"Inaccessible DBs: {len(all_dbs) - accessible_count}")
    print(f"Total documents across all accessible DBs: {total_documents}")
    
    # Find DBs with most data
    accessible_results = [r for r in results if r["accessible"]]
    if accessible_results:
        accessible_results.sort(key=lambda x: x["document_count"], reverse=True)
        print(f"\n📊 DBs with most documents:")
        for r in accessible_results[:5]:
            print(f"  • {r['name']}: {r['document_count']} documents ({r['size_mb']:.2f} MB)")
    
    # Check active DB
    try:
        from app.models.embeddings import VECTOR_DB
        active_path = VECTOR_DB._persist_directory
        active_name = Path(active_path).name
        
        active_result = next((r for r in results if r["name"] == active_name), None)
        if active_result:
            print(f"\n🎯 Active DB: {active_name}")
            if active_result["accessible"]:
                print(f"  • Documents: {active_result['document_count']}")
                print(f"  • Size: {active_result['size_mb']:.2f} MB")
            else:
                print(f"  • Status: INACCESSIBLE")
                print(f"  • Error: {active_result['error'][:100]}")
    except Exception as e:
        print(f"\n⚠️  Could not determine active DB: {e}")
    
    # Data loss assessment
    print("\n" + "=" * 70)
    print("Data Loss Assessment")
    print("=" * 70)
    
    if accessible_count == 0:
        print("❌ CRITICAL: No accessible databases found!")
        print("   All data may be lost or corrupted.")
    elif accessible_count == 1:
        active = next((r for r in results if r["accessible"]), None)
        if active:
            print(f"✅ Only one accessible DB: {active['name']}")
            print(f"   Documents: {active['document_count']}")
            if active['document_count'] == 0:
                print("   ⚠️  WARNING: Active DB is empty!")
    else:
        print(f"⚠️  Multiple accessible DBs found ({accessible_count})")
        print("   Data may be fragmented across multiple databases.")
        print("   Consider consolidating into single DB.")
    
    # Recovery recommendations
    print("\n" + "=" * 70)
    print("Recovery Recommendations")
    print("=" * 70)
    
    if accessible_count > 1:
        print("1. Consolidate data from all accessible DBs into active DB")
        print("2. Run: python scripts/recover_chromadb_data.py")
    elif accessible_count == 1:
        active = next((r for r in results if r["accessible"]), None)
        if active and active['document_count'] == 0:
            print("1. Active DB is empty - check if old DBs can be recovered")
            print("2. If recovery fails, re-ingest critical documents")
        else:
            print("1. Active DB has data - ensure backups are in place")
    else:
        print("1. Attempt manual recovery from corrupted DBs")
        print("2. Check if backups exist")
        print("3. Re-ingest critical documents")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

