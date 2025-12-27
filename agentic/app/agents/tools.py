"""
Tools for Agentic Agent
Same tools as structured RAG, but used dynamically by agent
"""
import sys
import os
from pathlib import Path

# Add parent directory to path to access main app models
parent_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(parent_dir))

# Import from main app (shared vector DB)
from app.models.embeddings import get_retriever
from langsmith import traceable

from app.models.llm_factory import summary_llm

llm = summary_llm(temperature=0.1)

@traceable(name="retrieve_tool", run_type="retriever")
def retrieve_tool(query: str, k: int = 10):
    """Retrieves top relevant chunks from vector DB."""
    retriever = get_retriever(k=k)
    if hasattr(retriever, 'invoke'):
        docs = retriever.invoke(query)
    else:
        docs = retriever.get_relevant_documents(query)
    return {
        "results": [d.page_content for d in docs],
        "count": len(docs),
    }

def summarize_tool(text: str):
    """Summarizes large text or retrieved chunks."""
    response = llm.invoke(f"Summarize the following text:\n\n{text}")
    return {"summary": response.content}

def keyword_search_tool(keyword: str):
    """Performs literal keyword search over stored documents."""
    retriever = get_retriever()
    all_docs = retriever.vectorstore._collection.get(include=["documents"])
    matches = [
        doc
        for doc in all_docs["documents"]
        if keyword.lower() in doc.lower()
    ]
    return {
        "keyword": keyword,
        "matches": matches,
        "count": len(matches),
    }

def metadata_search_tool(key: str, value: str):
    """Searches documents by metadata values."""
    retriever = get_retriever()
    data = retriever.vectorstore._collection.get(include=["metadatas", "documents"])
    results = []
    for meta, doc in zip(data["metadatas"], data["documents"]):
        if meta.get(key) == value:
            results.append(doc)
    return {
        "key": key,
        "value": value,
        "results": results,
        "count": len(results),
    }

