#!/usr/bin/env python3
"""
Chunking Strategy Evaluation Script

Evaluates chunking effectiveness across four metrics:
1. Retrieval Precision
2. Context Completeness
3. Boundary Issues
4. Citation Accuracy
"""

import json
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple
import re

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SEMANTIC_LIBS = True
except ImportError:
    HAS_SEMANTIC_LIBS = False
    print("Warning: sentence-transformers not available. Semantic evaluation disabled.")


class ChunkingEvaluator:
    """Evaluate chunking strategy effectiveness."""
    
    def __init__(self):
        if HAS_SEMANTIC_LIBS:
            self.semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
        else:
            self.semantic_model = None
    
    def evaluate_retrieval_precision(
        self, 
        query: str, 
        retrieved_chunks: List[str],
        threshold: float = 0.7
    ) -> Tuple[float, List[bool]]:
        """
        Evaluate if retrieved chunks are relevant to query.
        
        Returns:
            (precision_score, relevance_flags)
        """
        if not HAS_SEMANTIC_LIBS:
            # Fallback: simple keyword matching
            query_words = set(query.lower().split())
            relevance = []
            for chunk in retrieved_chunks:
                chunk_words = set(chunk.lower().split())
                overlap = len(query_words & chunk_words) / len(query_words) if query_words else 0
                relevance.append(overlap > 0.3)
            precision = sum(relevance) / len(relevance) if relevance else 0.0
            return precision, relevance
        
        # Semantic similarity approach
        query_embedding = self.semantic_model.encode(query)
        chunk_embeddings = self.semantic_model.encode(retrieved_chunks)
        similarities = cosine_similarity([query_embedding], chunk_embeddings)[0]
        
        relevance = [s > threshold for s in similarities]
        precision = sum(relevance) / len(relevance) if relevance else 0.0
        
        return precision, relevance
    
    def evaluate_completeness(
        self,
        expected_entities: List[str],
        answer: str
    ) -> float:
        """
        Check if answer contains all expected entities/information.
        
        Returns:
            Completeness score (0.0 to 1.0)
        """
        if not expected_entities:
            return 1.0
        
        found_entities = []
        answer_lower = answer.lower()
        
        for entity in expected_entities:
            if entity.lower() in answer_lower:
                found_entities.append(entity)
        
        completeness = len(found_entities) / len(expected_entities)
        return completeness
    
    def check_boundary_issues(self, chunks: List[str]) -> List[Dict[str, Any]]:
        """
        Detect if related concepts are split across chunks.
        
        Returns:
            List of boundary issues found
        """
        issues = []
        
        for i in range(len(chunks) - 1):
            chunk1_end = chunks[i][-100:] if len(chunks[i]) > 100 else chunks[i]
            chunk2_start = chunks[i+1][:100] if len(chunks[i+1]) > 100 else chunks[i+1]
            
            # Check for incomplete sentences
            if chunk1_end.strip() and not chunk1_end.rstrip().endswith(('.', '!', '?', ':', ';')):
                # Check if it's mid-sentence (has lowercase letter after last punctuation)
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
            if re.search(r'\d+\.\s*$', chunk1_end.strip()):
                if not chunk2_start.strip()[0].isdigit():
                    issues.append({
                        "type": "enumeration_split",
                        "chunk_index": i,
                        "description": f"Chunk {i} splits enumeration"
                    })
            
            # Check for split code blocks (if applicable)
            if '```' in chunk1_end and chunk1_end.count('```') % 2 != 0:
                issues.append({
                    "type": "code_block_split",
                    "chunk_index": i,
                    "description": f"Chunk {i} splits code block"
                })
        
        return issues
    
    def evaluate_semantic_coherence(self, chunks: List[str]) -> float:
        """
        Measure semantic similarity between adjacent chunks.
        
        Returns:
            Average coherence score (0.0 to 1.0)
        """
        if not HAS_SEMANTIC_LIBS or len(chunks) < 2:
            return 1.0
        
        coherence_scores = []
        for i in range(len(chunks) - 1):
            emb1 = self.semantic_model.encode(chunks[i])
            emb2 = self.semantic_model.encode(chunks[i+1])
            similarity = cosine_similarity([emb1], [emb2])[0][0]
            coherence_scores.append(similarity)
        
        avg_coherence = sum(coherence_scores) / len(coherence_scores) if coherence_scores else 1.0
        return avg_coherence
    
    def verify_citation(
        self,
        citation: Dict[str, Any],
        answer: str,
        document_text: str,
        chunk_text: str
    ) -> Tuple[bool, str]:
        """
        Verify if citation points to correct location.
        
        Returns:
            (is_accurate, reason)
        """
        start_index = citation.get("start_index", -1)
        chunk_id = citation.get("chunk_id", "")
        
        # Check if chunk text matches document at start_index
        if start_index >= 0:
            doc_slice = document_text[start_index:start_index + len(chunk_text)]
            if doc_slice != chunk_text[:len(doc_slice)]:
                return False, f"Start index {start_index} doesn't match chunk content"
        
        # Check if answer information appears in cited chunk
        answer_keywords = set(re.findall(r'\b\w{4,}\b', answer.lower()))
        chunk_keywords = set(re.findall(r'\b\w{4,}\b', chunk_text.lower()))
        
        overlap = len(answer_keywords & chunk_keywords)
        if overlap < len(answer_keywords) * 0.3:  # At least 30% keyword overlap
            return False, f"Low keyword overlap ({overlap}/{len(answer_keywords)})"
        
        return True, "Citation verified"
    
    def comprehensive_evaluation(
        self,
        test_cases: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Run comprehensive evaluation on test cases.
        
        Test case format:
        {
            "query": "question",
            "retrieved_chunks": ["chunk1", "chunk2", ...],
            "answer": "generated answer",
            "expected_entities": ["entity1", "entity2"],
            "document_text": "full document",
            "citations": [{"chunk_id": "...", "start_index": 123}]
        }
        """
        results = {
            "retrieval_precision": [],
            "completeness": [],
            "boundary_issues": [],
            "citation_accuracy": [],
            "semantic_coherence": []
        }
        
        for case in test_cases:
            query = case.get("query", "")
            chunks = case.get("retrieved_chunks", [])
            answer = case.get("answer", "")
            expected_entities = case.get("expected_entities", [])
            document_text = case.get("document_text", "")
            citations = case.get("citations", [])
            
            # 1. Retrieval Precision
            if chunks:
                precision, _ = self.evaluate_retrieval_precision(query, chunks)
                results["retrieval_precision"].append(precision)
            
            # 2. Completeness
            if expected_entities:
                completeness = self.evaluate_completeness(expected_entities, answer)
                results["completeness"].append(completeness)
            
            # 3. Boundary Issues
            if len(chunks) > 1:
                issues = self.check_boundary_issues(chunks)
                results["boundary_issues"].append({
                    "chunk_count": len(chunks),
                    "issue_count": len(issues),
                    "issues": issues
                })
            
            # 4. Citation Accuracy
            if citations and document_text:
                accurate_count = 0
                for citation in citations:
                    chunk_id = citation.get("chunk_id", "")
                    # Find chunk text (simplified - in real scenario, get from vector DB)
                    chunk_text = chunks[0] if chunks else ""  # Simplified
                    is_accurate, _ = self.verify_citation(
                        citation, answer, document_text, chunk_text
                    )
                    if is_accurate:
                        accurate_count += 1
                
                if citations:
                    accuracy = accurate_count / len(citations)
                    results["citation_accuracy"].append(accuracy)
            
            # 5. Semantic Coherence
            if len(chunks) > 1:
                coherence = self.evaluate_semantic_coherence(chunks)
                results["semantic_coherence"].append(coherence)
        
        # Calculate aggregate metrics
        summary = {
            "retrieval_precision": {
                "mean": sum(results["retrieval_precision"]) / len(results["retrieval_precision"]) if results["retrieval_precision"] else 0.0,
                "count": len(results["retrieval_precision"])
            },
            "completeness": {
                "mean": sum(results["completeness"]) / len(results["completeness"]) if results["completeness"] else 0.0,
                "count": len(results["completeness"])
            },
            "boundary_issues": {
                "total_chunks": sum(r["chunk_count"] for r in results["boundary_issues"]),
                "total_issues": sum(r["issue_count"] for r in results["boundary_issues"]),
                "issue_rate": sum(r["issue_count"] for r in results["boundary_issues"]) / sum(r["chunk_count"] for r in results["boundary_issues"]) if results["boundary_issues"] else 0.0
            },
            "citation_accuracy": {
                "mean": sum(results["citation_accuracy"]) / len(results["citation_accuracy"]) if results["citation_accuracy"] else 0.0,
                "count": len(results["citation_accuracy"])
            },
            "semantic_coherence": {
                "mean": sum(results["semantic_coherence"]) / len(results["semantic_coherence"]) if results["semantic_coherence"] else 0.0,
                "count": len(results["semantic_coherence"])
            }
        }
        
        return {
            "detailed_results": results,
            "summary": summary
        }


def main():
    parser = argparse.ArgumentParser(description="Evaluate chunking strategy")
    parser.add_argument("--test-queries", type=str, help="JSON file with test queries")
    parser.add_argument("--output", type=str, help="Output file for results")
    parser.add_argument("--metrics", type=str, default="all", 
                       choices=["all", "precision", "completeness", "boundary", "citation"],
                       help="Which metrics to evaluate")
    
    args = parser.parse_args()
    
    # Load test cases
    if args.test_queries:
        with open(args.test_queries, 'r') as f:
            test_cases = json.load(f)
    else:
        # Default test cases
        test_cases = [
            {
                "query": "What is authentication?",
                "retrieved_chunks": [
                    "Authentication is the process of verifying user identity.",
                    "It involves checking credentials against a database."
                ],
                "answer": "Authentication verifies user identity by checking credentials.",
                "expected_entities": ["authentication", "credentials"],
                "document_text": "Authentication is the process...",
                "citations": [{"chunk_id": "doc_0::chunk_0", "start_index": 0}]
            }
        ]
    
    # Run evaluation
    evaluator = ChunkingEvaluator()
    results = evaluator.comprehensive_evaluation(test_cases)
    
    # Print summary
    print("\n" + "="*60)
    print("CHUNKING EVALUATION RESULTS")
    print("="*60)
    
    summary = results["summary"]
    
    print(f"\n📊 Retrieval Precision: {summary['retrieval_precision']['mean']:.2%} "
          f"(n={summary['retrieval_precision']['count']})")
    print(f"📋 Completeness: {summary['completeness']['mean']:.2%} "
          f"(n={summary['completeness']['count']})")
    print(f"🔗 Boundary Issues: {summary['boundary_issues']['issue_rate']:.2%} "
          f"({summary['boundary_issues']['total_issues']}/{summary['boundary_issues']['total_chunks']} chunks)")
    print(f"📍 Citation Accuracy: {summary['citation_accuracy']['mean']:.2%} "
          f"(n={summary['citation_accuracy']['count']})")
    print(f"🔗 Semantic Coherence: {summary['semantic_coherence']['mean']:.2%} "
          f"(n={summary['semantic_coherence']['count']})")
    
    # Save results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n✅ Results saved to {args.output}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

