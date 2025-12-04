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

logger = logging.getLogger(__name__)

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
    
    This is different from structured RAG where tools are hardcoded.
    Here, the LLM analyzes the question and chooses the best tool.
    """
    question = state["question"]
    current_context = state.get("context", [])
    iteration = state.get("iteration_count", 0)
    
    # Build prompt for tool selection
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

Respond with ONLY the tool name (retrieve_tool, keyword_search_tool, metadata_search_tool, or summarize_tool).
If multiple tools might be useful, choose the most important one first.
"""
    
    try:
        response = agent_llm.invoke(prompt).content.strip()
        
        # Clean response to get tool name
        tool_name = response.lower().strip()
        if "retrieve" in tool_name:
            tool_name = "retrieve_tool"
        elif "keyword" in tool_name:
            tool_name = "keyword_search_tool"
        elif "metadata" in tool_name:
            tool_name = "metadata_search_tool"
        elif "summarize" in tool_name:
            tool_name = "summarize_tool"
        else:
            # Default to retrieve_tool
            tool_name = "retrieve_tool"
        
        state["tool_selection"] = tool_name
        logger.info(f"🤖 Agent selected tool: {tool_name} (iteration {iteration + 1})")
        
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

@traceable(name="tool_execution_node", run_type="tool")
def tool_execution_node(state: AgenticState) -> AgenticState:
    """
    AGENTIC: Execute the tool that the agent selected.
    
    This is dynamic - different tools execute based on agent's decision.
    In structured RAG, only retrieve_tool is used. Here, any tool can be used.
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
        # Dynamically execute the selected tool
        if tool_name == "retrieve_tool":
            result = retrieve_tool(question, k=5)
            # Add to context
            new_docs = result.get("results", [])
            state["context"] = current_context + new_docs
            
        elif tool_name == "keyword_search_tool":
            # Extract keyword from question (simple approach)
            keywords = [w for w in question.split() if len(w) > 4][:3]  # Top 3 keywords
            all_matches = []
            for keyword in keywords:
                result = keyword_search_tool(keyword)
                all_matches.extend(result.get("matches", []))
            state["context"] = current_context + all_matches
            
        elif tool_name == "metadata_search_tool":
            # Try to extract metadata from question
            # This is simplified - in production, use NER or structured extraction
            if "topic" in question.lower() or "category" in question.lower():
                # Extract topic/category from question
                result = metadata_search_tool("topic", "circuit_breaker")  # Simplified
                state["context"] = current_context + result.get("results", [])
            else:
                # Default behavior
                result = retrieve_tool(question, k=5)
                state["context"] = current_context + result.get("results", [])
                
        elif tool_name == "summarize_tool":
            # Summarize existing context
            if current_context:
                combined_context = "\n\n".join(current_context)
                result = summarize_tool(combined_context)
                summary = result.get("summary", "")
                state["context"] = [summary]  # Replace with summary
            else:
                # No context to summarize, retrieve instead
                result = retrieve_tool(question, k=5)
                state["context"] = result.get("results", [])
        else:
            # Fallback to retrieve
            result = retrieve_tool(question, k=5)
            state["context"] = current_context + result.get("results", [])
        
        state["tool_results"] = {"tool": tool_name, "success": True}
        logger.info(f"✅ Tool executed: {tool_name}, context now has {len(state['context'])} documents")
        
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
        state["tool_results"] = {"tool": tool_name, "success": False, "error": str(e)}
        # Fallback to retrieve
        result = retrieve_tool(question, k=5)
        state["context"] = current_context + result.get("results", [])
    
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
    
    This is the key to iterative refinement - the agent decides if it needs more information
    or if the answer is good enough.
    """
    question = state["question"]
    context = state.get("context", [])
    iteration = state.get("iteration_count", 0)
    answer = state.get("answer", "")
    
    # Prevent infinite loops
    if iteration >= 3:
        state["should_continue"] = "end"
        state["reasoning"] = "Maximum iterations reached"
        return state
    
    # If we have an answer, evaluate if it's complete
    if answer:
        prompt = f"""
You are evaluating whether an answer is complete and satisfactory.

Question: {question}
Current Answer: {answer}
Context Available: {len(context)} documents
Iteration: {iteration + 1}

Evaluate:
1. Is the answer complete and directly addresses the question?
2. Is there enough context to provide a good answer?
3. Would retrieving more information improve the answer?

Respond with ONE word:
- "end" if answer is complete and satisfactory
- "refine" if answer exists but needs improvement (get more context)
- "continue" if no answer yet and need more information
"""
    else:
        # No answer yet, check if we have enough context
        prompt = f"""
You are evaluating whether you have enough information to answer.

Question: {question}
Context Available: {len(context)} documents
Iteration: {iteration + 1}

Evaluate:
1. Do we have enough context to answer the question?
2. Should we retrieve more information?

Respond with ONE word:
- "continue" if need more information (retrieve more)
- "end" if have enough context to generate answer
"""
    
    try:
        response = decision_llm.invoke(prompt).content.strip().lower()
        
        if "end" in response:
            decision = "end"
            reasoning = "Have enough information to answer"
        elif "refine" in response:
            decision = "refine"
            reasoning = "Answer needs improvement, retrieving more context"
        else:
            decision = "continue"
            reasoning = "Need more information"
        
        state["should_continue"] = decision
        state["reasoning"] = reasoning
        state["iteration_count"] = iteration + 1
        
        logger.info(f"🧠 Agent reasoning: {reasoning} → {decision}")
        
    except Exception as e:
        logger.error(f"Error in reasoning: {e}", exc_info=True)
        # Default: end if we have context, continue if not
        if context:
            state["should_continue"] = "end"
        else:
            state["should_continue"] = "continue"
        state["iteration_count"] = iteration + 1
    
    return state


# ============================================================================
# STEP 6: GENERATE ANSWER NODE
# ============================================================================
# Why: Generate final answer from accumulated context
# ============================================================================

@traceable(name="generate_answer_node", run_type="llm")
def generate_answer_node(state: AgenticState) -> AgenticState:
    """
    Generate answer from accumulated context.
    Similar to structured RAG, but context comes from dynamic tool selection.
    """
    # Import memory from models
    from app.models.memory import Memory
    
    question = state["question"]
    context = "\n\n".join(state.get("context", []))
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
    
    This is the KEY difference from structured RAG:
    - Structured: Always same path
    - Agentic: Path changes based on LLM's reasoning
    
    Flow:
    - "continue" → Go back to tool_selection (get more info)
    - "refine" → Go back to tool_selection (improve answer)
    - "end" → Generate answer and finish
    """
    decision = state.get("should_continue", "end")
    iteration = state.get("iteration_count", 0)
    
    # Safety: prevent infinite loops
    if iteration >= 3:
        logger.warning("Max iterations reached, forcing end")
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
async def run_agentic_agent(session_id: str, question: str):
    """
    Run the agentic agent.
    
    This is different from structured RAG:
    - Structured: Fixed path, always same steps
    - Agentic: Dynamic path, LLM decides steps, can loop back
    """
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
        config={"metadata": {"session_id": session_id, "agentic": True}}
    )
    
    return result["answer"]

