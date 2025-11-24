# app/agents/doc_agent.py

from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langsmith import traceable

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



def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("generate", generate_node)
    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "generate")
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
        "answer": ""
    }
    # Use ainvoke for async graph execution (required when nodes are async)
    # LangGraph automatically traces the graph execution when LangSmith is enabled
    result = await AGENT.ainvoke(initial, config={"metadata": {"session_id": session_id}})
    return result["answer"]
