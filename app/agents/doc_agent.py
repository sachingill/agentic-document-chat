# app/agents/doc_agent.py

from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langsmith import traceable
import json

from app.models.memory import Memory
from app.agents.tools import retrieve_tool
from app.agents.reranker import rerank
import logging
logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    session_id: str
    question: str
    context: List[str]
    answer: str
    subqueries: List[str]  # Decomposed sub-queries
    merged_context: List[str]  # Merged context from all sub-queries


llm = ChatOpenAI(model="gpt-4o", temperature=0.1)


@traceable(name="retrieve_node", run_type="tool")
async def retrieve_node(state: AgentState) -> AgentState:
    question = state["question"]
    try:
        #--------- Vector search ---------
        res = retrieve_tool(question)
        docs = res["results"] if isinstance(res, dict) and "results" in res else []
        
        logger.info(f"Retrieved {len(docs)} documents from vector search")
        if docs:
            logger.debug(f"First retrieved doc: {docs[0][:100]}...")

        #--------- Rerank ---------
        if docs:
            ranked = await rerank(question, docs, top_k=3)
            state["context"] = ranked
            logger.info(f"After reranking: {len(ranked)} documents selected")
            if ranked:
                logger.debug(f"Top reranked doc: {ranked[0][:100]}...")
        else:
            logger.warning("No documents retrieved from vector search - empty context")
            state["context"] = []

    except Exception as e:
        # Handle retrieval errors gracefully (e.g., empty vector DB)
        logger.error(f"Error retrieving documents: {e}", exc_info=True)
        state["context"] = []
    return state


@traceable(name="generate_node", run_type="llm")
def generate_node(state: AgentState) -> AgentState:
    question = state["question"]
    context = "\n\n".join(state.get("context", []))
    session = state["session_id"]

    history = Memory.get_context(session)
    
    # Debug logging
    logger.info(f"Generating answer with {len(state.get('context', []))} context chunks")
    if not context or context.strip() == "":
        logger.warning("Empty context - LLM will respond 'I don't know'")

    prompt = f"""
You are a strict RAG assistant. 
Use ONLY the provided context to answer.

Context:
{context}

History:
{history}

Question:
{question}

RULES:
- If answer is not found in context, respond:
"I don't know based on the documents."
"""

    response = llm.invoke(prompt).content
    Memory.add_turn(session, question, response)

    state["answer"] = response
    return state

@traceable(name="decompose_node", run_type="chain")
def decompose_node(state: AgentState) -> AgentState:
    """
    Decomposition node: Breaks user query into 2-4 optimized sub-queries.
    """
    q = state["question"]
    prompt = f"""
You are a retrieval assistant
Your job is to break a user query into 2-4 optimized subqueries.
Rules:
- Keep them concise
- No hallucinations
- No rewriting domain text
- Do not ask questions back to user.
- Output JSON list only

User query: {q}
JSON:
"""
    try:  
        resp = llm.invoke(prompt).content.strip()
        
        # Clean response (remove markdown code blocks if present)
        if resp.startswith("```json"):
            resp = resp[7:]
        if resp.startswith("```"):
            resp = resp[3:]
        if resp.endswith("```"):
            resp = resp[:-3]
        resp = resp.strip()
        
        subqueries = json.loads(resp)
        
        # Validate: ensure it's a list
        if not isinstance(subqueries, list) or len(subqueries) == 0:
            raise ValueError("Invalid subqueries format")
        
        # Limit to 4 sub-queries max
        if len(subqueries) > 4:
            subqueries = subqueries[:4]
        
        state["subqueries"] = subqueries
        logger.info(f"Decomposed into {len(subqueries)} sub-queries: {subqueries}")
        
    except Exception as e:
        logger.error(f"Error decomposing query: {e}", exc_info=True)
        state["subqueries"] = [q]  # Fallback to original question
    
    return state


@traceable(name="multi_query_retrieve_node", run_type="tool")
def multi_query_retrieve_node(state: AgentState) -> AgentState:
    """
    Multi-query retrieval: Retrieves documents for each sub-query and merges results.
    This provides better coverage by retrieving from different query perspectives.
    """
    subqueries = state.get("subqueries", [])
    original_question = state["question"]
    
    if not subqueries:
        logger.warning("No subqueries found, using original question")
        subqueries = [original_question]
    
    all_docs = []
    seen_docs = set()  # For deduplication
    
    try:
        # Retrieve for each sub-query
        for i, subquery in enumerate(subqueries):
            logger.info(f"Retrieving for sub-query {i+1}/{len(subqueries)}: {subquery}")
            res = retrieve_tool(subquery, k=5)  # Get 5 docs per sub-query
            docs = res["results"] if isinstance(res, dict) and "results" in res else []
            
            # Deduplicate: add only if not seen before
            for doc in docs:
                # Use first 100 chars as a simple deduplication key
                doc_key = doc[:100] if len(doc) > 100 else doc
                if doc_key not in seen_docs:
                    seen_docs.add(doc_key)
                    all_docs.append(doc)
            
            logger.info(f"Retrieved {len(docs)} docs for sub-query {i+1}, total unique: {len(all_docs)}")
        
        state["merged_context"] = all_docs
        logger.info(f"Multi-query retrieval complete: {len(all_docs)} unique documents")
        
    except Exception as e:
        logger.error(f"Error in multi-query retrieval: {e}", exc_info=True)
        state["merged_context"] = []
    
    return state


@traceable(name="rerank_node", run_type="chain")
async def rerank_node(state: AgentState) -> AgentState:
    """
    Rerank node: Reranks and prunes the merged context from multi-query retrieval.
    """
    merged_docs = state.get("merged_context", [])
    original_question = state["question"]
    
    if not merged_docs:
        logger.warning("No documents to rerank")
        state["context"] = []
        return state
    
    try:
        # Rerank the merged documents
        ranked = await rerank(original_question, merged_docs, top_k=5)  # Top 5 after reranking
        state["context"] = ranked
        logger.info(f"Reranked {len(merged_docs)} docs down to {len(ranked)} top results")
        
    except Exception as e:
        logger.error(f"Error in reranking: {e}", exc_info=True)
        # Fallback: use first 5 docs
        state["context"] = merged_docs[:5]
    
    return state

def build_graph():
    """
    Build the agentic document chat graph with decomposition and multi-query retrieval.
    
    Flow:
    1. decompose → breaks query into 2-4 sub-queries
    2. multi_query_retrieve → retrieves for each sub-query and merges results
    3. rerank → reranks and prunes merged context
    4. generate → generates final answer
    5. END
    """
    graph = StateGraph(AgentState)
    
    # Add nodes
    graph.add_node("decompose", decompose_node)
    graph.add_node("multi_query_retrieve", multi_query_retrieve_node)
    graph.add_node("rerank", rerank_node)
    graph.add_node("generate", generate_node)
    
    # Set entry point to decomposition
    graph.set_entry_point("decompose")
    
    # Flow: decompose → multi_query_retrieve → rerank → generate → END
    graph.add_edge("decompose", "multi_query_retrieve")
    graph.add_edge("multi_query_retrieve", "rerank")
    graph.add_edge("rerank", "generate")
    graph.add_edge("generate", END)
    
    return graph.compile()


AGENT = build_graph()


@traceable(name="run_document_agent", run_type="chain")
async def run_document_agent(session_id: str, question: str):
    """
    Run the document agent asynchronously.
    Must be async because retrieve_node uses async reranking.
    
    This function is traced by LangSmith to monitor:
    - Full RAG pipeline execution
    - Session IDs for conversation tracking
    - Questions and answers
    - Performance metrics
    """
    initial = {
        "session_id": session_id,
        "question": question,
        "context": [],
        "answer": "",
        "subqueries": [],
        "merged_context": []
    }
    # Use ainvoke for async graph execution (required when nodes are async)
    # LangGraph automatically traces the graph execution when LangSmith is enabled
    result = await AGENT.ainvoke(initial, config={"metadata": {"session_id": session_id}})
    return result["answer"]
