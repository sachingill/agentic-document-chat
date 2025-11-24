# app/agents/tools.py

from app.models.embeddings import get_retriever
from langchain_openai import ChatOpenAI
from langsmith import traceable

# Use OpenAI for summarization / synthesis tools
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)


# 1. Retrieval tool (most important for RAG)
@traceable(name="retrieve_tool", run_type="retriever")
def retrieve_tool(query: str, k: int = 10):
    """
    Retrieves top relevant chunks from vector DB.
    
    Args:
        query: Search query
        k: Number of documents to retrieve (default 10, increased to give reranker more candidates)
    """
    retriever = get_retriever(k=k)
    # Use invoke() for newer LangChain versions, fallback to get_relevant_documents() for older versions
    if hasattr(retriever, 'invoke'):
        docs = retriever.invoke(query)
    else:
        docs = retriever.get_relevant_documents(query)

    return {
        "results": [d.page_content for d in docs],
        "count": len(docs),
    }


# 2. Summarization tool
def summarize_tool(text: str):
    """
    Summarizes large text or retrieved chunks.
    """
    response = llm.invoke(f"Summarize the following text:\n\n{text}")
    return {"summary": response.content}


# 3. Keyword search tool inside all stored docs
def keyword_search_tool(keyword: str):
    """
    Performs literal keyword search over stored documents.
    """
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


# 4. Metadata search tool
def metadata_search_tool(key: str, value: str):
    """
    Searches documents by metadata values (e.g., filename, page number).
    """
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
