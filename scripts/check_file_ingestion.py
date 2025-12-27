#!/usr/bin/env python3
"""
Check if a specific log file has been ingested into the vector database.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.models.embeddings import VECTOR_DB


def check_file_ingestion(filename: str):
    """Check if a file has been ingested by searching for documents with matching filename."""
    try:
        # Query the vector DB for documents with this filename
        # We'll use a simple text search first, then filter by metadata
        collection = VECTOR_DB._collection
        
        # Get all documents and filter by filename in metadata
        # Note: ChromaDB doesn't have a direct metadata filter in the Python API,
        # so we'll need to get results and filter
        
        # Try to get documents - ChromaDB's get() method with where filter
        try:
            # Use where clause to filter by filename
            results = collection.get(
                where={"filename": filename}
            )
            
            if results and results.get("ids"):
                count = len(results["ids"])
                print(f"✅ Found {count} documents ingested from '{filename}'")
                
                # Show sample metadata
                if results.get("metadatas"):
                    sample_meta = results["metadatas"][0] if results["metadatas"] else {}
                    print(f"\nSample metadata:")
                    for key, value in sample_meta.items():
                        print(f"  {key}: {value}")
                return True
            else:
                print(f"❌ No documents found for filename '{filename}'")
                return False
                
        except Exception as e:
            # Fallback: try searching by text content
            print(f"⚠️  Direct metadata query failed: {e}")
            print(f"Trying alternative method...")
            
            # Search for the filename in the collection
            try:
                # Get all documents (limited)
                all_results = collection.get(limit=10000)
                
                if all_results and all_results.get("metadatas"):
                    matching = []
                    for i, metadata in enumerate(all_results["metadatas"]):
                        if metadata and metadata.get("filename") == filename:
                            matching.append(i)
                    
                    if matching:
                        count = len(matching)
                        print(f"✅ Found {count} documents ingested from '{filename}'")
                        sample_meta = all_results["metadatas"][matching[0]]
                        print(f"\nSample metadata:")
                        for key, value in sample_meta.items():
                            print(f"  {key}: {value}")
                        return True
                    else:
                        print(f"❌ No documents found for filename '{filename}'")
                        print(f"\nChecked {len(all_results.get('metadatas', []))} documents in vector DB")
                        return False
                else:
                    print(f"❌ Could not retrieve documents from vector DB")
                    return False
                    
            except Exception as e2:
                print(f"❌ Error checking vector DB: {e2}")
                return False
                
    except Exception as e:
        print(f"❌ Error accessing vector DB: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 check_file_ingestion.py <filename>")
        print("Example: python3 check_file_ingestion.py catalina.part.aa.log")
        sys.exit(1)
    
    filename = sys.argv[1]
    print(f"Checking for file: {filename}\n")
    success = check_file_ingestion(filename)
    sys.exit(0 if success else 1)

