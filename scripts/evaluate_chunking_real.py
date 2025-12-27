#!/usr/bin/env python3
"""
Real Chunking Evaluation Script

This script actually queries your RAG system to evaluate chunking effectiveness.
It requires:
1. Documents already ingested in the vector database
2. Test queries (just questions, not pre-retrieved chunks)
3. Optionally: expected answers/entities for completeness evaluation
"""

import json
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from app.models.embeddings import get_retriever, VECTOR_DB
    from app.agents.tools import retrieve_tool
    HAS_RAG_SYSTEM = True
except ImportError as e:
    HAS_RAG_SYSTEM = False
    print(f"Warning: Could not import RAG system: {e}")
    print("Make sure you're running from the project root and dependencies are installed.")

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SEMANTIC_LIBS = True
except ImportError:
    HAS_SEMANTIC_LIBS = False
    print("Warning: sentence-transformers not available. Using keyword-based evaluation.")


class RealChunkingEvaluator:
    """Evaluate chunking using actual RAG system queries."""
    
    def __init__(self, api_url: str = None):
        """
        Initialize evaluator.
        
        Args:
            api_url: Optional API URL for querying via HTTP (if not using direct imports)
        """
        self.api_url = api_url
        if HAS_RAG_SYSTEM:
            self.retriever = get_retriever(k=5)  # Retrieve top 5 chunks
        if HAS_SEMANTIC_LIBS:
            self.semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
        else:
            self.semantic_model = None
    
    def query_rag_system(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Query the actual RAG system to get retrieved chunks.
        
        Returns:
            List of chunks with metadata: [{"text": "...", "metadata": {...}}]
        """
        if self.api_url:
            # Query via HTTP API
            import requests
            try:
                response = requests.post(
                    f"{self.api_url}/agent/chat",
                    json={"question": query, "session_id": "evaluation"},
                    timeout=30
                )
                if response.status_code == 200:
                    result = response.json()
                    # Extract chunks from response (adjust based on your API format)
                    return result.get("citations", [])
            except Exception as e:
                print(f"Error querying API: {e}")
                return []
        
        if HAS_RAG_SYSTEM:
            # Query directly using retriever
            try:
                docs = self.retriever.invoke(query) if hasattr(self.retriever, 'invoke') else self.retriever.get_relevant_documents(query)
                
                chunks = []
                for doc in docs:
                    chunks.append({
                        "text": doc.page_content,
                        "metadata": getattr(doc, "metadata", {}) or {}
                    })
                return chunks
            except Exception as e:
                print(f"Error querying vector DB: {e}")
                return []
        
        return []
    
    def evaluate_retrieval_precision(
        self, 
        query: str, 
        retrieved_chunks: List[Dict[str, Any]],
        threshold: float = 0.7
    ) -> Tuple[float, List[bool], List[str]]:
        """
        Evaluate if retrieved chunks are relevant to query.
        
        Returns:
            (precision_score, relevance_flags, chunk_texts)
        """
        if not retrieved_chunks:
            return 0.0, [], []
        
        chunk_texts = [chunk.get("text", "") for chunk in retrieved_chunks]
        
        if HAS_SEMANTIC_LIBS and self.semantic_model:
            # Semantic similarity approach
            query_embedding = self.semantic_model.encode(query)
            chunk_embeddings = self.semantic_model.encode(chunk_texts)
            similarities = cosine_similarity([query_embedding], chunk_embeddings)[0]
            
            relevance = [s > threshold for s in similarities]
            precision = sum(relevance) / len(relevance) if relevance else 0.0
            
            return precision, relevance, chunk_texts
        else:
            # Fallback: keyword matching
            query_words = set(query.lower().split())
            relevance = []
            for chunk_text in chunk_texts:
                chunk_words = set(chunk_text.lower().split())
                overlap = len(query_words & chunk_words) / len(query_words) if query_words else 0
                relevance.append(overlap > 0.3)
            precision = sum(relevance) / len(relevance) if relevance else 0.0
            return precision, relevance, chunk_texts
    
    def check_boundary_issues(self, chunks: List[str]) -> List[Dict[str, Any]]:
        """Detect boundary issues in chunks."""
        issues = []
        
        for i in range(len(chunks) - 1):
            chunk1_end = chunks[i][-100:] if len(chunks[i]) > 100 else chunks[i]
            chunk2_start = chunks[i+1][:100] if len(chunks[i+1]) > 100 else chunks[i+1]
            
            # Check for incomplete sentences
            if chunk1_end.strip() and not chunk1_end.rstrip().endswith(('.', '!', '?', ':', ';')):
                last_punct_idx = max(
                    chunk1_end.rfind('.'),
                    chunk1_end.rfind('!'),
                    chunk1_end.rfind('?'),
                    chunk1_end.rfind(':'),
                    chunk1_end.rfind(';')
                )
                if last_punct_idx >= 0:
                    after_punct = chunk1_end[last_punct_idx+1:].strip()
                    if after_punct and after_punct[0].islower():
                        issues.append({
                            "type": "mid_sentence_split",
                            "chunk_index": i,
                            "description": f"Chunk {i} ends mid-sentence"
                        })
            
            # Check for split enumerations
            import re
            if re.search(r'\d+\.\s*$', chunk1_end.strip()):
                if not chunk2_start.strip()[0].isdigit():
                    issues.append({
                        "type": "enumeration_split",
                        "chunk_index": i,
                        "description": f"Chunk {i} splits enumeration"
                    })
        
        return issues
    
    def evaluate_completeness(
        self,
        expected_entities: List[str],
        answer: str
    ) -> float:
        """Check if answer contains expected entities."""
        if not expected_entities:
            return 1.0
        
        found_entities = []
        answer_lower = answer.lower()
        
        for entity in expected_entities:
            if entity.lower() in answer_lower:
                found_entities.append(entity)
        
        completeness = len(found_entities) / len(expected_entities)
        return completeness
    
    def evaluate_chunking(
        self,
        test_queries: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluate chunking using real RAG system queries.
        
        Test query format:
        {
            "query": "question",
            "expected_entities": ["entity1", "entity2"],  # Optional
            "expected_answer": "expected answer text"  # Optional
        }
        """
        results = {
            "queries": [],
            "summary": {
                "retrieval_precision": [],
                "completeness": [],
                "boundary_issues": [],
                "total_chunks_retrieved": 0
            }
        }
        
        for idx, test_case in enumerate(test_queries):
            query = test_case.get("query", "")
            if not query:
                continue
            
            print(f"\n[{idx+1}/{len(test_queries)}] Evaluating: {query[:60]}...")
            
            # Query the actual RAG system
            retrieved_chunks = self.query_rag_system(query, k=5)
            
            if not retrieved_chunks:
                print(f"  ⚠️  No chunks retrieved for this query")
                continue
            
            chunk_texts = [chunk.get("text", "") for chunk in retrieved_chunks]
            chunk_metadata = [chunk.get("metadata", {}) for chunk in retrieved_chunks]
            
            # 1. Retrieval Precision
            precision, relevance_flags, _ = self.evaluate_retrieval_precision(query, retrieved_chunks)
            results["summary"]["retrieval_precision"].append(precision)
            
            # 2. Boundary Issues
            if len(chunk_texts) > 1:
                issues = self.check_boundary_issues(chunk_texts)
                issue_rate = len(issues) / len(chunk_texts) if chunk_texts else 0
                results["summary"]["boundary_issues"].append({
                    "chunk_count": len(chunk_texts),
                    "issue_count": len(issues),
                    "issue_rate": issue_rate,
                    "issues": issues
                })
            
            # 3. Completeness (if expected entities provided)
            completeness = None
            if test_case.get("expected_entities"):
                # Generate answer (simplified - in real scenario, use your RAG system)
                answer = " ".join(chunk_texts[:3])  # Simplified answer from top chunks
                completeness = self.evaluate_completeness(
                    test_case["expected_entities"],
                    answer
                )
                results["summary"]["completeness"].append(completeness)
            
            # Store query results
            query_result = {
                "query": query,
                "retrieved_chunks_count": len(retrieved_chunks),
                "retrieval_precision": precision,
                "relevance_flags": relevance_flags,
                "chunks": [
                    {
                        "text": text[:200] + "..." if len(text) > 200 else text,
                        "metadata": meta,
                        "relevant": rel
                    }
                    for text, meta, rel in zip(chunk_texts, chunk_metadata, relevance_flags)
                ]
            }
            
            if completeness is not None:
                query_result["completeness"] = completeness
            
            results["queries"].append(query_result)
            results["summary"]["total_chunks_retrieved"] += len(retrieved_chunks)
            
            print(f"  ✅ Retrieved {len(retrieved_chunks)} chunks, Precision: {precision:.2%}")
        
        # Calculate aggregate metrics
        if results["summary"]["retrieval_precision"]:
            results["summary"]["avg_precision"] = sum(results["summary"]["retrieval_precision"]) / len(results["summary"]["retrieval_precision"])
        else:
            results["summary"]["avg_precision"] = 0.0
        
        if results["summary"]["completeness"]:
            results["summary"]["avg_completeness"] = sum(results["summary"]["completeness"]) / len(results["summary"]["completeness"])
        else:
            results["summary"]["avg_completeness"] = None
        
        if results["summary"]["boundary_issues"]:
            total_chunks = sum(b["chunk_count"] for b in results["summary"]["boundary_issues"])
            total_issues = sum(b["issue_count"] for b in results["summary"]["boundary_issues"])
            results["summary"]["boundary_issue_rate"] = total_issues / total_chunks if total_chunks > 0 else 0.0
        else:
            results["summary"]["boundary_issue_rate"] = 0.0
        
        return results


def main():
    parser = argparse.ArgumentParser(description="Evaluate chunking using real RAG system")
    parser.add_argument("--test-queries", type=str, required=True,
                       help="JSON file with test queries (just questions)")
    parser.add_argument("--output", type=str, help="Output file for results")
    parser.add_argument("--api-url", type=str, help="API URL for querying via HTTP (optional)")
    
    args = parser.parse_args()
    
    # Load test queries
    with open(args.test_queries, 'r') as f:
        test_queries = json.load(f)
    
    if not isinstance(test_queries, list):
        print("Error: Test queries must be a JSON array")
        return 1
    
    # Check if documents are ingested
    if HAS_RAG_SYSTEM:
        try:
            count = VECTOR_DB._collection.count()
            print(f"📊 Vector DB contains {count} documents")
            if count == 0:
                print("⚠️  Warning: No documents in vector DB. Please ingest documents first.")
                print("   Use: python scripts/ingest_sample_logs.py")
                return 1
        except Exception as e:
            print(f"⚠️  Could not check vector DB: {e}")
    
    # Run evaluation
    evaluator = RealChunkingEvaluator(api_url=args.api_url)
    results = evaluator.evaluate_chunking(test_queries)
    
    # Print summary
    print("\n" + "="*60)
    print("CHUNKING EVALUATION RESULTS")
    print("="*60)
    
    summary = results["summary"]
    
    print(f"\n📊 Average Retrieval Precision: {summary['avg_precision']:.2%}")
    print(f"   (Based on {len(summary['retrieval_precision'])} queries)")
    
    if summary['avg_completeness'] is not None:
        print(f"\n📋 Average Completeness: {summary['avg_completeness']:.2%}")
        print(f"   (Based on {len(summary['completeness'])} queries)")
    
    print(f"\n🔗 Boundary Issue Rate: {summary['boundary_issue_rate']:.2%}")
    if summary['boundary_issues']:
        total_chunks = sum(b["chunk_count"] for b in summary['boundary_issues'])
        total_issues = sum(b["issue_count"] for b in summary['boundary_issues'])
        print(f"   ({total_issues} issues in {total_chunks} chunks)")
    
    print(f"\n📚 Total Chunks Retrieved: {summary['total_chunks_retrieved']}")
    
    # Save results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n✅ Detailed results saved to {args.output}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

