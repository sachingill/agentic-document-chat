#!/usr/bin/env python3
"""
Recover and consolidate data from all ChromaDB instances.

This script:
1. Checks all ChromaDB directories for accessible data
2. Recovers documents from all accessible databases
3. Consolidates into a single safe database
4. Updates the system to use the recovered database
5. Backs up before making changes
"""

import os
import sys
import shutil
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
from datetime import datetime

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


def check_db(db_path: Path) -> Tuple[bool, int, Chroma]:
    """Check if a ChromaDB is accessible and return instance."""
    try:
        db = Chroma(
            persist_directory=str(db_path),
            collection_name="doc",
            embedding_function=EMBEDDINGS
        )
        count = db._collection.count()
        return True, count, db
    except Exception as e:
        return False, 0, None


def get_all_documents(db: Chroma) -> List[Dict]:
    """Extract all documents from a ChromaDB instance."""
    try:
        # Get all documents using get() method
        all_data = db._collection.get()
        
        documents = []
        ids = all_data.get("ids", [])
        texts = all_data.get("documents", [])
        metadatas = all_data.get("metadatas", [])
        
        for i, doc_id in enumerate(ids):
            documents.append({
                "id": doc_id,
                "text": texts[i] if i < len(texts) else "",
                "metadata": metadatas[i] if i < len(metadatas) else {}
            })
        
        return documents
    except Exception as e:
        print(f"  ⚠️  Error extracting documents: {e}")
        # Fallback: try to retrieve using retriever
        try:
            retriever = db.as_retriever(search_kwargs={"k": 10000})  # Large k to get all
            docs = retriever.get_relevant_documents("")  # Empty query
            
            documents = []
            for doc in docs:
                documents.append({
                    "id": doc.metadata.get("chunk_id", f"doc_{len(documents)}"),
                    "text": doc.page_content,
                    "metadata": doc.metadata or {}
                })
            return documents
        except Exception as e2:
            print(f"  ❌ Fallback retrieval also failed: {e2}")
            return []


def deduplicate_documents(all_documents: List[Dict]) -> List[Dict]:
    """Remove duplicate documents based on chunk_id or content hash."""
    seen_ids: Set[str] = set()
    seen_content: Set[str] = set()
    unique_docs = []
    
    for doc in all_documents:
        # Use chunk_id if available, otherwise use content hash
        doc_id = doc.get("id") or doc.get("metadata", {}).get("chunk_id")
        content = doc.get("text", "")
        
        # Check both ID and content for deduplication
        if doc_id and doc_id not in seen_ids:
            seen_ids.add(doc_id)
            unique_docs.append(doc)
        elif content and content not in seen_content:
            seen_content.add(content)
            unique_docs.append(doc)
    
    return unique_docs


def create_backup(db_path: Path) -> Path:
    """Create a backup of a database directory."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = Path(f"{db_path}_backup_{timestamp}")
    
    if db_path.exists():
        try:
            shutil.copytree(db_path, backup_path)
            return backup_path
        except Exception as e:
            print(f"  ⚠️  Backup failed: {e}")
            return None
    return None


def main():
    print("=" * 70)
    print("ChromaDB Data Recovery and Consolidation")
    print("=" * 70)
    
    # Find all DBs
    all_dbs = []
    main_db = project_root / "ragdb"
    if main_db.exists():
        all_dbs.append(main_db)
    
    fresh_dbs = sorted(project_root.glob("ragdb_fresh_*"))
    all_dbs.extend(fresh_dbs)
    
    if not all_dbs:
        print("\n❌ No ChromaDB directories found")
        return 1
    
    print(f"\n📊 Found {len(all_dbs)} ChromaDB directories")
    
    # Step 1: Check all databases
    print("\n" + "=" * 70)
    print("Step 1: Checking all databases for accessible data")
    print("=" * 70)
    
    accessible_dbs = []
    total_documents_found = 0
    
    for db_path in all_dbs:
        is_accessible, count, db = check_db(db_path)
        status = "✅ ACCESSIBLE" if is_accessible else "❌ INACCESSIBLE"
        print(f"{status:20} | {db_path.name:40} | {count:6} documents")
        
        if is_accessible and count > 0:
            accessible_dbs.append((db_path, count, db))
            total_documents_found += count
    
    if not accessible_dbs:
        print("\n❌ No accessible databases with data found!")
        print("   Data recovery is not possible.")
        return 1
    
    print(f"\n✅ Found {len(accessible_dbs)} accessible databases")
    print(f"   Total documents across all DBs: {total_documents_found}")
    
    # Step 2: Recover documents from all accessible DBs
    print("\n" + "=" * 70)
    print("Step 2: Recovering documents from all accessible databases")
    print("=" * 70)
    
    all_recovered_documents = []
    
    for db_path, count, db in accessible_dbs:
        print(f"\n📥 Recovering from {db_path.name} ({count} documents)...")
        documents = get_all_documents(db)
        
        if documents:
            print(f"  ✅ Recovered {len(documents)} documents")
            all_recovered_documents.extend(documents)
        else:
            print(f"  ⚠️  No documents recovered")
    
    print(f"\n📊 Total documents recovered: {len(all_recovered_documents)}")
    
    # Step 3: Deduplicate
    print("\n" + "=" * 70)
    print("Step 3: Deduplicating recovered documents")
    print("=" * 70)
    
    unique_documents = deduplicate_documents(all_recovered_documents)
    duplicates_removed = len(all_recovered_documents) - len(unique_documents)
    
    print(f"  • Total recovered: {len(all_recovered_documents)}")
    print(f"  • After deduplication: {len(unique_documents)}")
    print(f"  • Duplicates removed: {duplicates_removed}")
    
    if not unique_documents:
        print("\n❌ No unique documents to recover!")
        return 1
    
    # Step 4: Create safe recovery database
    print("\n" + "=" * 70)
    print("Step 4: Creating safe recovery database")
    print("=" * 70)
    
    recovery_db_path = project_root / "ragdb_recovered"
    
    # Backup existing recovery DB if it exists
    if recovery_db_path.exists():
        print(f"  📦 Backing up existing recovery DB...")
        backup = create_backup(recovery_db_path)
        if backup:
            print(f"  ✅ Backup created: {backup.name}")
        shutil.rmtree(recovery_db_path)
    
    print(f"  🔄 Creating recovery database at: {recovery_db_path.name}")
    
    try:
        recovery_db = Chroma(
            persist_directory=str(recovery_db_path),
            collection_name="doc",
            embedding_function=EMBEDDINGS
        )
        
        # Prepare documents for ingestion
        texts = [doc["text"] for doc in unique_documents]
        metadatas = [doc["metadata"] for doc in unique_documents]
        ids = [doc["id"] for doc in unique_documents]
        
        # Ingest in batches to avoid memory issues
        batch_size = 100
        total_batches = (len(texts) + batch_size - 1) // batch_size
        
        print(f"  📥 Ingesting {len(texts)} documents in {total_batches} batches...")
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_metadatas = metadatas[i:i + batch_size]
            batch_ids = ids[i:i + batch_size]
            
            recovery_db.add_texts(
                texts=batch_texts,
                metadatas=batch_metadatas,
                ids=batch_ids
            )
            
            batch_num = (i // batch_size) + 1
            print(f"    ✅ Batch {batch_num}/{total_batches} ingested ({len(batch_texts)} documents)")
        
        recovery_db.persist()
        
        # Verify recovery
        recovered_count = recovery_db._collection.count()
        print(f"\n  ✅ Recovery database created successfully!")
        print(f"     Documents in recovery DB: {recovered_count}")
        
        if recovered_count != len(unique_documents):
            print(f"  ⚠️  Warning: Count mismatch (expected {len(unique_documents)}, got {recovered_count})")
        
    except Exception as e:
        print(f"\n  ❌ Error creating recovery database: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Step 5: Backup current active DB and switch to recovered DB
    print("\n" + "=" * 70)
    print("Step 5: Switching to recovered database")
    print("=" * 70)
    
    # Get current active DB
    try:
        from app.models.embeddings import VECTOR_DB
        current_active_path = Path(VECTOR_DB._persist_directory).resolve()
        print(f"  📍 Current active DB: {current_active_path.name}")
        
        # Backup current active DB
        if current_active_path.exists():
            print(f"  📦 Backing up current active DB...")
            backup = create_backup(current_active_path)
            if backup:
                print(f"  ✅ Backup created: {backup.name}")
        
    except Exception as e:
        print(f"  ⚠️  Could not determine active DB: {e}")
        current_active_path = None
    
    # Step 6: Update system to use recovered DB
    print("\n" + "=" * 70)
    print("Step 6: Finalizing recovery")
    print("=" * 70)
    
    # Create a safe production DB
    production_db_path = project_root / "ragdb"
    
    # Backup existing production DB
    if production_db_path.exists() and production_db_path != recovery_db_path:
        print(f"  📦 Backing up existing production DB...")
        backup = create_backup(production_db_path)
        if backup:
            print(f"  ✅ Backup created: {backup.name}")
        shutil.rmtree(production_db_path)
    
    # Copy recovered DB to production location
    print(f"  🔄 Copying recovery DB to production location...")
    shutil.copytree(recovery_db_path, production_db_path)
    
    # Verify production DB
    try:
        prod_db = Chroma(
            persist_directory=str(production_db_path),
            collection_name="doc",
            embedding_function=EMBEDDINGS
        )
        prod_count = prod_db._collection.count()
        print(f"  ✅ Production DB verified: {prod_count} documents")
    except Exception as e:
        print(f"  ❌ Error verifying production DB: {e}")
        return 1
    
    # Summary
    print("\n" + "=" * 70)
    print("Recovery Complete!")
    print("=" * 70)
    print(f"✅ Recovered {len(unique_documents)} unique documents")
    print(f"✅ Consolidated into single database: {production_db_path.name}")
    print(f"✅ System will use recovered database on next restart")
    print(f"\n📝 Next steps:")
    print(f"   1. Restart the application to use recovered database")
    print(f"   2. Verify data is accessible via API/UI")
    print(f"   3. Run cleanup script to remove old databases (optional)")
    print(f"      python scripts/cleanup_old_chromadb.py")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

