# app/agents/doc_agent.py

from typing import TypedDict, List, Optional, Any
from langgraph.graph import StateGraph, END
from langsmith import traceable
import json

from app.models.memory import Memory
from app.agents.tools import retrieve_tool
from app.agents.reranker import rerank
from app.agents.inference_modes import InferenceMode, INFERENCE_CONFIGS
from app.agents.inference_utils import expand_queries, verify_supported, IDK_SENTINEL, normalize_mixed_idk
from app.models.llm_factory import main_llm
import logging
logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    session_id: str
    question: str
    inference_mode: InferenceMode
    context: List[dict[str, Any]]  # selected chunks with metadata
    answer: str
    subqueries: List[str]  # Decomposed sub-queries
    merged_context: List[dict[str, Any]]  # Merged context from all sub-queries
    citations: List[dict[str, Any]]  # final citations returned to API


llm = main_llm(temperature=0.1)


@traceable(name="retrieve_node", run_type="tool")
async def retrieve_node(state: AgentState) -> AgentState:
    question = state["question"]
    try:
        #--------- Vector search ---------
        res = retrieve_tool(question)
        docs = res.get("documents") if isinstance(res, dict) else None
        if not isinstance(docs, list):
            # Back-compat fallback
            texts = res["results"] if isinstance(res, dict) and "results" in res else []
            docs = [{"text": t, "metadata": {}} for t in texts]
        
        logger.info(f"Retrieved {len(docs)} documents from vector search")
        if docs:
            logger.debug(f"First retrieved doc: {str(docs[0].get('text',''))[:100]}...")

        #--------- Rerank ---------
        if docs:
            ranked = await rerank(question, docs, top_k=3)
            state["context"] = ranked
            logger.info(f"After reranking: {len(ranked)} documents selected")
            if ranked:
                logger.debug(f"Top reranked doc: {str(ranked[0].get('text',''))[:100]}...")
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
    chunks = state.get("context", [])
    context = "\n\n".join([str(c.get("text", "")) for c in chunks])
    session = state["session_id"]
    mode: InferenceMode = state.get("inference_mode", "balanced")  # type: ignore
    cfg = INFERENCE_CONFIGS.get(mode, INFERENCE_CONFIGS["balanced"])

    history = Memory.get_context(session)
    
    # Debug logging
    logger.info(f"Generating answer with {len(state.get('context', []))} context chunks")
    if not context or context.strip() == "":
        logger.warning("Empty context - LLM will respond 'I don't know'")

    # Evidence gate (high-strictness): if evidence is too thin, don't even attempt synthesis.
    if mode == "high" and len(state.get("context", [])) < cfg.min_chunks:
        response = IDK_SENTINEL
        Memory.add_turn(session, question, response)
        state["answer"] = response
        return state

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
    response = normalize_mixed_idk(response)

    # Optional verifier step (balanced/high): if the answer isn't supported, downgrade to IDK.
    if cfg.verify_answer and response.strip() != IDK_SENTINEL and context.strip():
        verdict = verify_supported(question=question, context=context[:8000], answer=response)
        if verdict.get("supported") is False:
            logger.info(f"Verifier rejected answer; returning IDK. reason={verdict.get('reason')}")
            response = IDK_SENTINEL

    Memory.add_turn(session, question, response)

    state["answer"] = response
    # Attach citations (top chunks used)
    state["citations"] = [
        {
            "text": c.get("text", "")[:500],
            "metadata": c.get("metadata") or {},
        }
        for c in chunks
    ]
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

    # Normalize subqueries in case the LLM returns a list of dicts like:
    # [{"subquery": "..."}, {"query": "..."}]
    normalized: list[str] = []
    for sq in subqueries:
        if isinstance(sq, str):
            s = sq.strip()
            if s:
                normalized.append(s)
            continue
        if isinstance(sq, dict):
            val = sq.get("subquery") or sq.get("query") or sq.get("q")
            if isinstance(val, str) and val.strip():
                normalized.append(val.strip())
            continue
        # Fallback: stringify
        s = str(sq).strip()
        if s:
            normalized.append(s)

    if not normalized:
        normalized = [original_question]
    subqueries = normalized
    
    all_docs: list[dict[str, Any]] = []
    seen_keys: set[str] = set()  # For deduplication
    mode: InferenceMode = state.get("inference_mode", "balanced")  # type: ignore
    cfg = INFERENCE_CONFIGS.get(mode, INFERENCE_CONFIGS["balanced"])
    
    try:
        # Retrieve for each sub-query
        for i, subquery in enumerate(subqueries):
            logger.info(f"Retrieving for sub-query {i+1}/{len(subqueries)}: {subquery}")
            res = retrieve_tool(subquery, k=max(5, cfg.base_k // max(1, len(subqueries))))  # distribute budget
            docs = res.get("documents") if isinstance(res, dict) else None
            if not isinstance(docs, list):
                texts = res["results"] if isinstance(res, dict) and "results" in res else []
                docs = [{"text": t, "metadata": {}} for t in texts]
            
            # Deduplicate: add only if not seen before
            for doc in docs:
                meta = doc.get("metadata") or {}
                key = meta.get("chunk_id") or meta.get("chunk_id".upper())  # defensive
                if not isinstance(key, str) or not key:
                    text = str(doc.get("text", ""))
                    key = text[:120]
                if key not in seen_keys:
                    seen_keys.add(key)
                    all_docs.append(doc)
            
            logger.info(f"Retrieved {len(docs)} docs for sub-query {i+1}, total unique: {len(all_docs)}")

        # Second-pass retrieval if evidence is thin (common cause of "I don't know")
        if len(all_docs) < cfg.min_chunks:
            logger.info(f"Second-pass retrieval triggered (mode={mode}, have={len(all_docs)}, need={cfg.min_chunks})")
            for q in expand_queries(original_question, mode=mode)[1:]:
                res2 = retrieve_tool(q, k=cfg.second_pass_k)
                docs2 = res2.get("documents") if isinstance(res2, dict) else None
                if not isinstance(docs2, list):
                    texts2 = res2["results"] if isinstance(res2, dict) and "results" in res2 else []
                    docs2 = [{"text": t, "metadata": {}} for t in texts2]
                for doc in docs2:
                    meta = doc.get("metadata") or {}
                    key = meta.get("chunk_id") or str(doc.get("text", ""))[:120]
                    if key not in seen_keys:
                        seen_keys.add(key)
                        all_docs.append(doc)
            logger.info(f"Second-pass retrieval complete: total unique={len(all_docs)}")
        
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


@traceable(name="run_document_agent_with_citations", run_type="chain")
async def run_document_agent_with_citations(
    session_id: str,
    question: str,
    inference_mode: InferenceMode = "balanced",
) -> dict[str, Any]:
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
        "inference_mode": inference_mode,
        "context": [],
        "answer": "",
        "subqueries": [],
        "merged_context": [],
        "citations": [],
    }
    # Use ainvoke for async graph execution (required when nodes are async)
    # LangGraph automatically traces the graph execution when LangSmith is enabled
    # Include session_id + question in LangSmith metadata so we can attach user feedback later.
    result = await AGENT.ainvoke(
        initial,
        config={"metadata": {"session_id": session_id, "question": question, "inference_mode": inference_mode}},
    )
    return {"answer": result.get("answer", ""), "citations": result.get("citations", [])}


# Backwards-compatible API: return answer string only.
@traceable(name="run_document_agent", run_type="chain")
async def run_document_agent(session_id: str, question: str, inference_mode: InferenceMode = "balanced") -> str:
    result = await run_document_agent_with_citations(session_id, question, inference_mode=inference_mode)
    return str(result.get("answer", ""))
