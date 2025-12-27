#!/usr/bin/env python3
"""
Ingest Training Dataset

This script ingests a high-quality training dataset for testing RAG accuracy.
It includes diverse documents and corresponding test queries with ground truth answers.

Steps:
1. Load training documents
2. Ingest documents into vector DB
3. Load test queries
4. Optionally run evaluation
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.models.embeddings import ingest_documents


def load_training_documents(file_path: Path) -> tuple[List[str], List[Dict[str, Any]]]:
    """
    Load training documents from JSON file.
    
    Returns:
        (texts, metadatas) - Lists ready for ingestion
    """
    print(f"📄 Loading training documents from {file_path}...")
    
    with open(file_path, 'r') as f:
        docs = json.load(f)
    
    texts = []
    metadatas = []
    
    for doc in docs:
        content = doc.get("content", "")
        if not content:
            continue
        
        texts.append(content)
        
        # Build rich metadata
        metadata = {
            "doc_id": doc.get("doc_id", ""),
            "title": doc.get("title", ""),
            "category": doc.get("category", ""),
            "tags": ", ".join(doc.get("tags", [])),
            "source": "training_dataset",
            "type": "training_document",
        }
        metadatas.append(metadata)
    
    print(f"✅ Loaded {len(texts)} training documents")
    return texts, metadatas


def ingest_training_dataset(documents_file: Path):
    """
    Ingest training documents into vector database.
    
    Args:
        documents_file: Path to training_documents.json
    """
    print("\n" + "="*60)
    print("TRAINING DATASET INGESTION")
    print("="*60)
    
    # Load documents
    texts, metadatas = load_training_documents(documents_file)
    
    if not texts:
        print("❌ No documents to ingest")
        return False
    
    # Show summary
    print(f"\n📊 Dataset Summary:")
    categories = {}
    for meta in metadatas:
        cat = meta.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1
    
    for category, count in sorted(categories.items()):
        print(f"  • {category}: {count} documents")
    
    # Ingest documents
    print(f"\n🔄 Ingesting {len(texts)} documents into vector DB...")
    try:
        ingest_documents(texts, metadata=metadatas)
        print(f"✅ Successfully ingested {len(texts)} training documents")
        return True
    except Exception as e:
        print(f"❌ Error ingesting documents: {e}")
        import traceback
        traceback.print_exc()
        return False


def load_test_queries(file_path: Path) -> List[Dict[str, Any]]:
    """
    Load test queries with ground truth answers.
    
    Returns:
        List of test query dictionaries
    """
    print(f"\n📋 Loading test queries from {file_path}...")
    
    with open(file_path, 'r') as f:
        queries = json.load(f)
    
    print(f"✅ Loaded {len(queries)} test queries")
    
    # Show summary by difficulty
    difficulties = {}
    categories = {}
    for q in queries:
        diff = q.get("difficulty", "unknown")
        cat = q.get("category", "unknown")
        difficulties[diff] = difficulties.get(diff, 0) + 1
        categories[cat] = categories.get(cat, 0) + 1
    
    print(f"\n📊 Test Queries Summary:")
    print(f"  By Difficulty:")
    for diff, count in sorted(difficulties.items()):
        print(f"    • {diff}: {count} queries")
    print(f"  By Category:")
    for cat, count in sorted(categories.items()):
        print(f"    • {cat}: {count} queries")
    
    return queries


def main():
    parser = argparse.ArgumentParser(description="Ingest training dataset for RAG evaluation")
    parser.add_argument("--documents", type=str, 
                       default="samples/training_documents.json",
                       help="Path to training documents JSON file")
    parser.add_argument("--queries", type=str,
                       default="samples/training_queries_with_answers.json",
                       help="Path to test queries JSON file")
    parser.add_argument("--evaluate", action="store_true",
                       help="Run evaluation after ingestion")
    
    args = parser.parse_args()
    
    documents_file = project_root / args.documents
    queries_file = project_root / args.queries
    
    # Check files exist
    if not documents_file.exists():
        print(f"❌ Documents file not found: {documents_file}")
        return 1
    
    if not queries_file.exists():
        print(f"❌ Queries file not found: {queries_file}")
        return 1
    
    # Ingest documents
    success = ingest_training_dataset(documents_file)
    if not success:
        return 1
    
    # Load test queries
    test_queries = load_test_queries(queries_file)
    
    print(f"\n✅ Training dataset ready!")
    print(f"\n📝 Next steps:")
    print(f"  1. Run evaluation: python scripts/evaluate_chunking_real.py --test-queries {args.queries}")
    print(f"  2. Test queries manually via UI or API")
    print(f"  3. Compare results with expected answers")
    
    # Optionally run evaluation
    if args.evaluate:
        print(f"\n🔄 Running evaluation...")
        from scripts.evaluate_chunking_real import RealChunkingEvaluator
        
        evaluator = RealChunkingEvaluator()
        results = evaluator.evaluate_chunking(test_queries)
        
        # Print summary
        summary = results["summary"]
        print(f"\n📊 Evaluation Results:")
        print(f"  Average Precision: {summary['avg_precision']:.2%}")
        if summary['avg_completeness']:
            print(f"  Average Completeness: {summary['avg_completeness']:.2%}")
        print(f"  Boundary Issue Rate: {summary['boundary_issue_rate']:.2%}")
    
    return 0


if __name__ == "__main__":
    import argparse
    sys.exit(main())

