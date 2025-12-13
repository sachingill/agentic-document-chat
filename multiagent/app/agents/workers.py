"""
Worker Agents

Specialized workers that execute specific tasks as delegated by the supervisor.
"""

from typing import Dict, Any
from langsmith import traceable
import logging
import sys
from pathlib import Path

# Add parent directory to path to import tools
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
from app.agents.tools import retrieve_tool, keyword_search_tool, metadata_search_tool

# Import LLM factory for multi-provider support
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from multiagent.app.models.llm_providers import create_fast_llm, create_reasoning_llm

logger = logging.getLogger(__name__)

# LLMs for workers
worker_llm = create_fast_llm(temperature=0.1)
analysis_llm = create_reasoning_llm(temperature=0.1)


@traceable(name="retrieval_worker", run_type="tool")
def retrieval_worker_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Retrieval Worker: Specialized document retrieval.
    
    Focuses on gathering comprehensive information from documents.
    """
    question = state.get("question", "")
    worker_results = state.get("worker_results", {})
    
    logger.info("📚 Retrieval Worker: Gathering documents...")
    
    try:
        # Use retrieve_tool for semantic search
        result = retrieve_tool(question, k=10)
        docs = result.get("results", [])
        
        # Format result
        if docs:
            answer = f"Retrieved {len(docs)} documents:\n\n" + "\n\n".join(docs[:5])
        else:
            answer = "No documents found."
        
        worker_results["RetrievalWorker"] = {
            "answer": answer,
            "doc_count": len(docs),
            "docs": docs[:5]  # Store top 5
        }
        state["worker_results"] = worker_results
        
        logger.info(f"✅ Retrieval Worker: Retrieved {len(docs)} documents")
        
    except Exception as e:
        logger.error(f"❌ Retrieval Worker error: {e}", exc_info=True)
        worker_results["RetrievalWorker"] = {
            "answer": f"Error: {str(e)}",
            "doc_count": 0
        }
        state["worker_results"] = worker_results
    
    return state


@traceable(name="analysis_worker", run_type="chain")
def analysis_worker_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analysis Worker: Information analysis and structuring.
    
    Analyzes retrieved information and structures it logically.
    """
    question = state.get("question", "")
    worker_results = state.get("worker_results", {})
    
    logger.info("📊 Analysis Worker: Analyzing information...")
    
    try:
        # Get retrieval results if available
        retrieval_result = worker_results.get("RetrievalWorker", {})
        docs = retrieval_result.get("docs", [])
        
        if not docs:
            # Try to retrieve documents ourselves
            result = retrieve_tool(question, k=5)
            docs = result.get("results", [])
        
        if docs:
            context = "\n\n".join(docs)
            
            # Analyze with LLM
            analysis_prompt = f"""
Analyze the following documents and extract structured information relevant to the question.

Question: {question}

Documents:
{context}

Extract:
1. Key points relevant to the question
2. Important relationships
3. Structured analysis

Provide a clear, structured analysis.
"""
            answer = analysis_llm.invoke(analysis_prompt).content.strip()
        else:
            answer = "No documents available for analysis."
        
        worker_results["AnalysisWorker"] = {
            "answer": answer,
            "analysis_type": "structured"
        }
        state["worker_results"] = worker_results
        
        logger.info("✅ Analysis Worker: Analysis complete")
        
    except Exception as e:
        logger.error(f"❌ Analysis Worker error: {e}", exc_info=True)
        worker_results["AnalysisWorker"] = {
            "answer": f"Error: {str(e)}",
            "analysis_type": "error"
        }
        state["worker_results"] = worker_results
    
    return state


@traceable(name="code_worker", run_type="chain")
def code_worker_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Code Worker: Code-related queries and examples.
    
    Focuses on finding code examples and implementation details.
    """
    question = state.get("question", "")
    worker_results = state.get("worker_results", {})
    
    logger.info("💻 Code Worker: Searching for code examples...")
    
    try:
        # Search for code-related content
        # Use keyword search for code-related terms
        code_keywords = ["code", "implementation", "example", "function", "class", "method"]
        all_docs = []
        
        for keyword in code_keywords[:2]:  # Limit to 2 keywords
            if keyword.lower() in question.lower():
                result = keyword_search_tool(keyword)
                matches = result.get("matches", [])
                all_docs.extend(matches)
        
        # Also try semantic search
        if not all_docs:
            result = retrieve_tool(question, k=5)
            docs = result.get("results", [])
            all_docs.extend(docs)
        
        if all_docs:
            context = "\n\n".join(all_docs[:5])
            
            code_prompt = f"""
Extract code examples and implementation details from the following documents.

Question: {question}

Documents:
{context}

Extract:
1. Code examples if available
2. Implementation details
3. Code-related explanations

Provide code examples and implementation details.
"""
            answer = worker_llm.invoke(code_prompt).content.strip()
        else:
            answer = "No code examples found."
        
        worker_results["CodeWorker"] = {
            "answer": answer,
            "code_found": len(all_docs) > 0
        }
        state["worker_results"] = worker_results
        
        logger.info(f"✅ Code Worker: Found {len(all_docs)} code-related documents")
        
    except Exception as e:
        logger.error(f"❌ Code Worker error: {e}", exc_info=True)
        worker_results["CodeWorker"] = {
            "answer": f"Error: {str(e)}",
            "code_found": False
        }
        state["worker_results"] = worker_results
    
    return state


@traceable(name="comparison_worker", run_type="chain")
def comparison_worker_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Comparison Worker: Compare multiple topics or concepts.
    
    Focuses on finding similarities, differences, and relationships.
    """
    question = state.get("question", "")
    worker_results = state.get("worker_results", {})
    
    logger.info("⚖️ Comparison Worker: Comparing topics...")
    
    try:
        # Retrieve documents
        result = retrieve_tool(question, k=10)
        docs = result.get("results", [])
        
        if docs:
            context = "\n\n".join(docs)
            
            comparison_prompt = f"""
Compare and analyze the topics mentioned in the question.

Question: {question}

Documents:
{context}

Extract:
1. Similarities between topics
2. Differences between topics
3. Use cases for each
4. When to use which

Provide a structured comparison.
"""
            answer = analysis_llm.invoke(comparison_prompt).content.strip()
        else:
            answer = "No documents available for comparison."
        
        worker_results["ComparisonWorker"] = {
            "answer": answer,
            "comparison_type": "structured"
        }
        state["worker_results"] = worker_results
        
        logger.info("✅ Comparison Worker: Comparison complete")
        
    except Exception as e:
        logger.error(f"❌ Comparison Worker error: {e}", exc_info=True)
        worker_results["ComparisonWorker"] = {
            "answer": f"Error: {str(e)}",
            "comparison_type": "error"
        }
        state["worker_results"] = worker_results
    
    return state


@traceable(name="explanation_worker", run_type="chain")
def explanation_worker_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Explanation Worker: Conceptual explanations and definitions.
    
    Focuses on providing clear explanations and definitions.
    """
    question = state.get("question", "")
    worker_results = state.get("worker_results", {})
    
    logger.info("📖 Explanation Worker: Generating explanation...")
    
    try:
        # Retrieve documents
        result = retrieve_tool(question, k=5)
        docs = result.get("results", [])
        
        if docs:
            context = "\n\n".join(docs)
            
            explanation_prompt = f"""
Provide a clear, comprehensive explanation based on the documents.

Question: {question}

Documents:
{context}

Provide:
1. Clear definition
2. Key concepts
3. Important details
4. Examples if available

Make it easy to understand.
"""
            answer = worker_llm.invoke(explanation_prompt).content.strip()
        else:
            answer = "No documents available for explanation."
        
        worker_results["ExplanationWorker"] = {
            "answer": answer,
            "explanation_type": "conceptual"
        }
        state["worker_results"] = worker_results
        
        logger.info("✅ Explanation Worker: Explanation complete")
        
    except Exception as e:
        logger.error(f"❌ Explanation Worker error: {e}", exc_info=True)
        worker_results["ExplanationWorker"] = {
            "answer": f"Error: {str(e)}",
            "explanation_type": "error"
        }
        state["worker_results"] = worker_results
    
    return state


