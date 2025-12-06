"""
AGENTIC RAG AGENT - Fully Agentic Implementation

This is a TRUE agentic system where:
1. LLM decides which tools to use
2. Conditional routing based on decisions
3. Iterative refinement (can loop back)
4. Dynamic tool selection
5. Reasoning about next steps

DIFFERENCES FROM STRUCTURED RAG:
- Structured: Fixed flow, hardcoded tools
- Agentic: Dynamic flow, LLM chooses tools, can refine
"""

from typing import TypedDict, List, Optional, Literal
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langsmith import traceable
import json
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from parent directory (only for local development)
# In production, environment variables should be set on the hosting platform
parent_dir = Path(__file__).parent.parent.parent.parent
env_path = parent_dir / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

logger = logging.getLogger(__name__)

# Configuration
MAX_ITERATIONS = int(os.getenv("AGENTIC_MAX_ITERATIONS", "3"))
MAX_CONTEXT_DOCS = int(os.getenv("AGENTIC_MAX_CONTEXT_DOCS", "15"))  # Limit context size
CONTEXT_DEDUP_THRESHOLD = 100  # Characters to use for deduplication key

# ============================================================================
# STEP 1: ENHANCED AGENT STATE
# ============================================================================
# Why: Need to track agent decisions, tool usage, and reasoning
# ============================================================================

class AgenticState(TypedDict):
    session_id: str
    question: str
    context: List[str]  # Accumulated context from all tool calls
    answer: str
    tool_selection: Optional[str]  # Which tool was selected
    tool_results: Optional[dict]  # Results from tool execution
    reasoning: Optional[str]  # Agent's reasoning about next steps
    iteration_count: int  # Track iterations to prevent infinite loops
    should_continue: Optional[Literal["continue", "refine", "end"]]  # Decision for routing


# ============================================================================
# STEP 2: LLM FOR AGENTIC DECISIONS
# ============================================================================
# Why: Need a reasoning LLM that can make decisions
# ============================================================================

agent_llm = ChatOpenAI(model="gpt-4o", temperature=0.1)  # Main reasoning LLM
decision_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)  # Fast decision LLM


# ============================================================================
# STEP 3: TOOL SELECTION NODE (AGENTIC!)
# ============================================================================
# Why: LLM decides which tool(s) to use based on question type
# This is the KEY difference - LLM makes the decision, not hardcoded
# ============================================================================

@traceable(name="tool_selection_node", run_type="chain")
def tool_selection_node(state: AgenticState) -> AgenticState:
    """
    AGENTIC: LLM decides which tool to use based on the question.
    
    IMPROVED: Uses structured JSON output for more reliable parsing.
    """
    question = state["question"]
    current_context = state.get("context", [])
    iteration = state.get("iteration_count", 0)
    
    # Build prompt for tool selection with structured output
    tools_description = """
Available tools:
1. retrieve_tool - Search documents using semantic similarity (best for general questions)
2. keyword_search_tool - Exact keyword matching (best for specific terms/names)
3. metadata_search_tool - Search by metadata (best for filtering by category/topic)
4. summarize_tool - Summarize existing context (best when context is too long)

Current context: """ + (str(len(current_context)) + " documents" if current_context else "None")
    
    prompt = f"""
You are an intelligent agent that decides which tool to use for answering questions.

Question: {question}
Iteration: {iteration + 1}

{tools_description}

Analyze the question and decide which tool is most appropriate.
Consider:
- Question type (general vs specific)
- Whether you need semantic search or exact matching
- If you already have context, might need summarization
- If question asks for specific metadata (category, topic, etc.)

Respond with a JSON object in this exact format:
{{
    "tool": "retrieve_tool" | "keyword_search_tool" | "metadata_search_tool" | "summarize_tool",
    "reasoning": "brief explanation of why this tool was chosen"
}}
"""
    
    try:
        response = decision_llm.invoke(prompt).content.strip()
        
        # Parse JSON response (more robust than string matching)
        # Remove markdown code blocks if present
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            response = response.split("```")[1].split("```")[0].strip()
        
        try:
            result = json.loads(response)
            tool_name = result.get("tool", "retrieve_tool")
            reasoning = result.get("reasoning", "No reasoning provided")
            
            # Validate tool name
            valid_tools = ["retrieve_tool", "keyword_search_tool", "metadata_search_tool", "summarize_tool"]
            if tool_name not in valid_tools:
                logger.warning(f"Invalid tool name '{tool_name}', defaulting to retrieve_tool")
                tool_name = "retrieve_tool"
            
            state["tool_selection"] = tool_name
            logger.info(f"🤖 Agent selected tool: {tool_name} (iteration {iteration + 1}) - {reasoning}")
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}, falling back to string matching")
            # Fallback to string matching
            response_lower = response.lower()
            if "retrieve" in response_lower:
                tool_name = "retrieve_tool"
            elif "keyword" in response_lower:
                tool_name = "keyword_search_tool"
            elif "metadata" in response_lower:
                tool_name = "metadata_search_tool"
            elif "summarize" in response_lower:
                tool_name = "summarize_tool"
            else:
                tool_name = "retrieve_tool"
            state["tool_selection"] = tool_name
            logger.info(f"🤖 Agent selected tool: {tool_name} (iteration {iteration + 1}) [fallback]")
        
    except Exception as e:
        logger.error(f"Error in tool selection: {e}", exc_info=True)
        state["tool_selection"] = "retrieve_tool"  # Fallback
    
    return state


# ============================================================================
# STEP 4: TOOL EXECUTION NODE (DYNAMIC!)
# ============================================================================
# Why: Execute the tool that LLM selected (not hardcoded)
# This executes different tools based on agent's decision
# ============================================================================

def _deduplicate_context(context: List[str]) -> List[str]:
    """Remove duplicate documents from context using content-based deduplication."""
    seen = set()
    deduplicated = []
    for doc in context:
        # Use first N characters as deduplication key
        doc_key = doc[:CONTEXT_DEDUP_THRESHOLD].strip().lower()
        if doc_key and doc_key not in seen:
            seen.add(doc_key)
            deduplicated.append(doc)
    return deduplicated


def _limit_context_size(context: List[str], max_docs: int = MAX_CONTEXT_DOCS) -> List[str]:
    """Limit context to max_docs, keeping the most recent ones."""
    if len(context) <= max_docs:
        return context
    logger.info(f"Limiting context from {len(context)} to {max_docs} documents")
    return context[-max_docs:]


def _extract_keywords_llm(question: str) -> List[str]:
    """Extract meaningful keywords from question using LLM (improved over naive extraction)."""
    prompt = f"""
Extract 2-3 meaningful keywords from this question that would be useful for exact keyword search.
Focus on:
- Technical terms
- Proper nouns (names, places, products)
- Important concepts
- Avoid common words like "what", "how", "is", "the"

Question: {question}

Respond with a JSON array of keywords:
["keyword1", "keyword2", "keyword3"]
"""
    try:
        response = decision_llm.invoke(prompt).content.strip()
        # Remove markdown code blocks if present
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            response = response.split("```")[1].split("```")[0].strip()
        
        keywords = json.loads(response)
        if isinstance(keywords, list) and len(keywords) > 0:
            return keywords[:3]  # Limit to 3 keywords
    except Exception as e:
        logger.warning(f"Failed to extract keywords with LLM: {e}, using fallback")
    
    # Fallback: simple extraction (improved from original)
    words = question.split()
    # Filter out common stop words and short words
    stop_words = {"what", "how", "is", "are", "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
    keywords = [w.lower().strip(".,!?;:") for w in words if len(w) > 4 and w.lower() not in stop_words]
    return keywords[:3]


def _extract_metadata_llm(question: str) -> Optional[dict]:
    """Extract metadata (key, value) from question using LLM (fixes hardcoded bug)."""
    prompt = f"""
Extract metadata filters from this question if it mentions specific categories, topics, or metadata fields.

Question: {question}

If the question asks for documents with specific metadata (like "topic", "category", "type", etc.),
respond with JSON:
{{
    "key": "metadata_key_name",
    "value": "metadata_value"
}}

If no metadata is mentioned, respond with:
{{
    "key": null,
    "value": null
}}
"""
    try:
        response = decision_llm.invoke(prompt).content.strip()
        # Remove markdown code blocks if present
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            response = response.split("```")[1].split("```")[0].strip()
        
        result = json.loads(response)
        if result.get("key") and result.get("value"):
            return {"key": result["key"], "value": result["value"]}
    except Exception as e:
        logger.warning(f"Failed to extract metadata with LLM: {e}")
    
    return None


@traceable(name="tool_execution_node", run_type="tool")
def tool_execution_node(state: AgenticState) -> AgenticState:
    """
    AGENTIC: Execute the tool that the agent selected.
    
    IMPROVED:
    - Better keyword extraction using LLM
    - Dynamic metadata extraction (fixes hardcoded bug)
    - Context deduplication
    - Context size limiting
    """
    # Import tools from same directory
    from .tools import (
        retrieve_tool, 
        keyword_search_tool, 
        metadata_search_tool, 
        summarize_tool
    )
    
    tool_name = state.get("tool_selection", "retrieve_tool")
    question = state["question"]
    current_context = state.get("context", [])
    
    logger.info(f"🔧 Executing tool: {tool_name}")
    
    try:
        new_docs = []
        
        # Dynamically execute the selected tool
        if tool_name == "retrieve_tool":
            result = retrieve_tool(question, k=5)
            new_docs = result.get("results", [])
            
        elif tool_name == "keyword_search_tool":
            # IMPROVED: Use LLM to extract meaningful keywords
            keywords = _extract_keywords_llm(question)
            logger.info(f"Extracted keywords: {keywords}")
            
            all_matches = []
            for keyword in keywords:
                result = keyword_search_tool(keyword)
                all_matches.extend(result.get("matches", []))
            new_docs = all_matches
            
        elif tool_name == "metadata_search_tool":
            # IMPROVED: Extract metadata dynamically from question (fixes hardcoded bug)
            metadata = _extract_metadata_llm(question)
            
            if metadata and metadata.get("key") and metadata.get("value"):
                logger.info(f"Extracted metadata: {metadata['key']}={metadata['value']}")
                result = metadata_search_tool(metadata["key"], metadata["value"])
                new_docs = result.get("results", [])
            else:
                # No metadata found, fallback to retrieve
                logger.info("No metadata found in question, falling back to retrieve_tool")
                result = retrieve_tool(question, k=5)
                new_docs = result.get("results", [])
                
        elif tool_name == "summarize_tool":
            # Summarize existing context
            if current_context:
                combined_context = "\n\n".join(current_context)
                result = summarize_tool(combined_context)
                summary = result.get("summary", "")
                state["context"] = [summary]  # Replace with summary
                state["tool_results"] = {"tool": tool_name, "success": True}
                logger.info(f"✅ Tool executed: {tool_name}, context summarized to 1 document")
                return state
            else:
                # No context to summarize, retrieve instead
                result = retrieve_tool(question, k=5)
                new_docs = result.get("results", [])
        else:
            # Fallback to retrieve
            result = retrieve_tool(question, k=5)
            new_docs = result.get("results", [])
        
        # IMPROVED: Add new docs to context with deduplication
        combined_context = current_context + new_docs
        deduplicated = _deduplicate_context(combined_context)
        state["context"] = _limit_context_size(deduplicated, MAX_CONTEXT_DOCS)
        
        state["tool_results"] = {"tool": tool_name, "success": True}
        logger.info(f"✅ Tool executed: {tool_name}, context now has {len(state['context'])} documents (after dedup)")
        
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
        state["tool_results"] = {"tool": tool_name, "success": False, "error": str(e)}
        # Fallback to retrieve
        try:
            result = retrieve_tool(question, k=5)
            new_docs = result.get("results", [])
            combined_context = current_context + new_docs
            state["context"] = _limit_context_size(_deduplicate_context(combined_context), MAX_CONTEXT_DOCS)
        except Exception as fallback_error:
            logger.error(f"Fallback retrieval also failed: {fallback_error}")
            state["context"] = current_context  # Keep existing context
    
    return state


# ============================================================================
# STEP 5: REASONING NODE (AGENTIC!)
# ============================================================================
# Why: LLM evaluates if answer is complete or needs more information
# This enables iterative refinement
# ============================================================================

@traceable(name="reasoning_node", run_type="chain")
def reasoning_node(state: AgenticState) -> AgenticState:
    """
    AGENTIC: LLM reasons about whether to continue, refine, or end.
    
    IMPROVED:
    - Uses structured JSON output for more reliable parsing
    - Configurable max iterations
    - Early termination if context is sufficient
    """
    question = state["question"]
    context = state.get("context", [])
    iteration = state.get("iteration_count", 0)
    answer = state.get("answer", "")
    
    # IMPROVED: Use configurable max iterations
    if iteration >= MAX_ITERATIONS:
        state["should_continue"] = "end"
        state["reasoning"] = f"Maximum iterations ({MAX_ITERATIONS}) reached"
        logger.warning(f"Max iterations ({MAX_ITERATIONS}) reached, forcing end")
        return state
    
    # IMPROVED: Early termination if we have sufficient context
    if len(context) >= MAX_CONTEXT_DOCS and iteration > 0:
        state["should_continue"] = "end"
        state["reasoning"] = f"Sufficient context gathered ({len(context)} documents)"
        state["iteration_count"] = iteration + 1
        logger.info(f"Early termination: sufficient context ({len(context)} docs)")
        return state
    
    # If we have an answer, evaluate if it's complete
    if answer:
        prompt = f"""
You are evaluating whether an answer is complete and satisfactory.

Question: {question}
Current Answer: {answer}
Context Available: {len(context)} documents
Iteration: {iteration + 1} / {MAX_ITERATIONS}

Evaluate:
1. Is the answer complete and directly addresses the question?
2. Is there enough context to provide a good answer?
3. Would retrieving more information improve the answer?

Respond with JSON:
{{
    "decision": "end" | "refine" | "continue",
    "reasoning": "brief explanation"
}}
"""
    else:
        # No answer yet, check if we have enough context
        prompt = f"""
You are evaluating whether you have enough information to answer.

Question: {question}
Context Available: {len(context)} documents
Iteration: {iteration + 1} / {MAX_ITERATIONS}

Evaluate:
1. Do we have enough context to answer the question?
2. Should we retrieve more information?

Respond with JSON:
{{
    "decision": "continue" | "end",
    "reasoning": "brief explanation"
}}
"""
    
    try:
        response = decision_llm.invoke(prompt).content.strip()
        
        # IMPROVED: Parse JSON response (more robust)
        # Remove markdown code blocks if present
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            response = response.split("```")[1].split("```")[0].strip()
        
        try:
            result = json.loads(response)
            decision = result.get("decision", "end").lower()
            reasoning = result.get("reasoning", "No reasoning provided")
            
            # Validate decision
            valid_decisions = ["continue", "refine", "end"]
            if decision not in valid_decisions:
                logger.warning(f"Invalid decision '{decision}', defaulting to 'end'")
                decision = "end"
            
            state["should_continue"] = decision
            state["reasoning"] = reasoning
            state["iteration_count"] = iteration + 1
            
            logger.info(f"🧠 Agent reasoning: {reasoning} → {decision}")
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}, falling back to string matching")
            # Fallback to string matching
            response_lower = response.lower()
            if "end" in response_lower and ("refine" not in response_lower and "continue" not in response_lower):
                decision = "end"
                reasoning = "Have enough information to answer"
            elif "refine" in response_lower:
                decision = "refine"
                reasoning = "Answer needs improvement, retrieving more context"
            else:
                decision = "continue"
                reasoning = "Need more information"
            
            state["should_continue"] = decision
            state["reasoning"] = reasoning
            state["iteration_count"] = iteration + 1
            logger.info(f"🧠 Agent reasoning: {reasoning} → {decision} [fallback]")
        
    except Exception as e:
        logger.error(f"Error in reasoning: {e}", exc_info=True)
        # Default: end if we have context, continue if not
        if context:
            state["should_continue"] = "end"
            state["reasoning"] = "Error in reasoning, defaulting to end (have context)"
        else:
            state["should_continue"] = "continue"
            state["reasoning"] = "Error in reasoning, defaulting to continue (no context)"
        state["iteration_count"] = iteration + 1
    
    return state


# ============================================================================
# STEP 6: GENERATE ANSWER NODE
# ============================================================================
# Why: Generate final answer from accumulated context
# ============================================================================

@traceable(name="rerank_context_node", run_type="chain")
async def rerank_context_node(state: AgenticState) -> AgenticState:
    """
    IMPROVED: Rerank context before generation (like structured RAG).
    This improves answer quality by ensuring most relevant documents are used.
    """
    question = state["question"]
    context = state.get("context", [])
    
    if not context:
        logger.warning("No context to rerank")
        return state
    
    # Import reranker from parent app
    import sys
    from pathlib import Path
    parent_dir = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(parent_dir))
    from app.agents.reranker import rerank
    
    try:
        # Rerank and keep top 5 most relevant documents
        ranked = await rerank(question, context, top_k=5)
        state["context"] = ranked
        logger.info(f"✅ Context reranked: {len(context)} → {len(ranked)} documents")
    except Exception as e:
        logger.error(f"Error reranking context: {e}", exc_info=True)
        # Keep original context if reranking fails
        state["context"] = context[:5]  # At least limit to 5
    
    return state


@traceable(name="generate_answer_node", run_type="llm")
async def generate_answer_node(state: AgenticState) -> AgenticState:
    """
    Generate answer from accumulated context.
    
    IMPROVED:
    - Reranks context before generation (like structured RAG)
    - Limits context size to prevent token overflow
    """
    # IMPROVED: Rerank context before generation
    state = await rerank_context_node(state)
    
    # Import memory from models
    from app.models.memory import Memory
    
    question = state["question"]
    context_list = state.get("context", [])
    
    # IMPROVED: Limit context to prevent token overflow
    if len(context_list) > 5:
        logger.info(f"Limiting context from {len(context_list)} to 5 documents for generation")
        context_list = context_list[:5]
    
    context = "\n\n".join(context_list)
    session = state["session_id"]
    
    history = Memory.get_context(session)
    
    prompt = f"""
You are a RAG assistant. Use ONLY the provided context to answer.

Context:
{context}

History:
{history}

Question:
{question}

RULES:
- If answer is not found in context, respond: "I don't know based on the documents."
- Be concise and accurate
"""
    
    try:
        response = agent_llm.invoke(prompt).content
        Memory.add_turn(session, question, response)
        state["answer"] = response
        logger.info(f"✅ Answer generated: {len(response)} chars")
    except Exception as e:
        logger.error(f"Error generating answer: {e}", exc_info=True)
        state["answer"] = "I encountered an error while generating the answer."
    
    return state


# ============================================================================
# STEP 7: CONDITIONAL ROUTING FUNCTION (AGENTIC!)
# ============================================================================
# Why: Route based on LLM's decision (continue/refine/end)
# This enables dynamic flow - different paths based on agent's reasoning
# ============================================================================

def should_continue(state: AgenticState) -> Literal["tool_selection", "generate", "end"]:
    """
    AGENTIC: Conditional routing based on agent's decision.
    
    IMPROVED: Uses configurable max iterations
    """
    decision = state.get("should_continue", "end")
    iteration = state.get("iteration_count", 0)
    
    # IMPROVED: Use configurable max iterations
    if iteration >= MAX_ITERATIONS:
        logger.warning(f"Max iterations ({MAX_ITERATIONS}) reached, forcing end")
        return "end"
    
    if decision == "continue":
        logger.info("🔄 Routing: continue → tool_selection (get more info)")
        return "tool_selection"
    elif decision == "refine":
        logger.info("🔄 Routing: refine → tool_selection (improve answer)")
        return "tool_selection"
    else:  # "end"
        logger.info("🔄 Routing: end → generate (finalize answer)")
        return "generate"


# ============================================================================
# STEP 8: BUILD AGENTIC GRAPH
# ============================================================================
# Why: Create the graph with conditional routing (not fixed edges!)
# ============================================================================

def build_agentic_graph():
    """
    Build the AGENTIC graph with conditional routing.
    
    KEY DIFFERENCES FROM STRUCTURED RAG:
    1. Uses conditional_edges (not fixed edges)
    2. Can loop back (iterative refinement)
    3. LLM decides the path
    """
    graph = StateGraph(AgenticState)
    
    # Add nodes
    graph.add_node("tool_selection", tool_selection_node)  # LLM chooses tool
    graph.add_node("tool_execution", tool_execution_node)  # Execute chosen tool
    graph.add_node("reasoning", reasoning_node)  # LLM reasons about next step
    graph.add_node("generate", generate_answer_node)  # Generate final answer
    
    # Set entry point
    graph.set_entry_point("tool_selection")
    
    # AGENTIC: Fixed edges for tool execution flow
    graph.add_edge("tool_selection", "tool_execution")
    graph.add_edge("tool_execution", "reasoning")
    
    # AGENTIC: Conditional routing based on LLM decision
    graph.add_conditional_edges(
        "reasoning",
        should_continue,  # Function that returns next node based on state
        {
            "tool_selection": "tool_selection",  # Loop back to get more info
            "generate": "generate",  # Generate answer
            "end": END  # End (shouldn't happen, but safety)
        }
    )
    
    # Final edge
    graph.add_edge("generate", END)
    
    return graph.compile()


# ============================================================================
# STEP 9: RUN AGENTIC AGENT
# ============================================================================

AGENTIC_AGENT = build_agentic_graph()


@traceable(name="run_agentic_agent", run_type="chain")
async def run_agentic_agent(session_id: str, question: str, max_iterations: Optional[int] = None):
    """
    Run the agentic agent.
    
    IMPROVED:
    - Configurable max_iterations parameter
    - Better logging of iterations and tool usage
    
    This is different from structured RAG:
    - Structured: Fixed path, always same steps
    - Agentic: Dynamic path, LLM decides steps, can loop back
    """
    # Use provided max_iterations or default from config
    global MAX_ITERATIONS
    original_max = MAX_ITERATIONS
    if max_iterations is not None:
        MAX_ITERATIONS = max_iterations
        logger.info(f"Using custom max_iterations: {max_iterations}")
    
    try:
        initial = {
            "session_id": session_id,
            "question": question,
            "context": [],
            "answer": "",
            "tool_selection": None,
            "tool_results": None,
            "reasoning": None,
            "iteration_count": 0,
            "should_continue": None
        }
        
        result = await AGENTIC_AGENT.ainvoke(
            initial, 
            config={"metadata": {
                "session_id": session_id, 
                "agentic": True,
                "max_iterations": MAX_ITERATIONS
            }}
        )
        
        # Log final statistics
        final_iterations = result.get("iteration_count", 0)
        final_context_size = len(result.get("context", []))
        tools_used = result.get("tool_selection", "unknown")
        logger.info(f"✅ Agentic agent completed: {final_iterations} iterations, {final_context_size} context docs, tool: {tools_used}")
        
        return result["answer"]
    finally:
        # Restore original max_iterations
        MAX_ITERATIONS = original_max