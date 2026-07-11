"""
core/agent.py  —  Cardinal Agent Core
 
Flusso del grafo:
 
  START
    │
    ▼
  cardinal_node  ──► (has tool_calls?)  ──► tools_node
    ▲                      │ no                │
    │                      ▼                   │
    │                     END                  │
    └──────────────────────────────────────────┘
  (after every tool, returns to the cardinal node)

MemorySaver keeps the history in RAM.
In the future, it can be replaced with SqliteSaver or RedisCheckpointer
for persistence across sessions
"""

import logging
import typing

from langchain_core.messages import SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from config.settings import Settings
from core.llm import LLMBackend
from core.personality import CARDINAL_SYSTEM_PROMPT
from tools.base import get_tools

logger = logging.getLogger(__name__)

def build_agent(settings: Settings, backend: typing.Optional[LLMBackend] = None):
    """
    Builds and compiles the Cardinal LangGraph graph.

    Args:
        settings: project configuration (read from .env)
        backend:  an already initialized LLMBackend — if None, a new one is created

    Returns:
        CompiledStateGraph ready for .invoke() and .stream()
    """

    if (backend is None):
        backend = LLMBackend(settings)
    # #endif

    tools = get_tools()
    llm_with_tools = backend.with_tools(tools)

    def cardinal_node(state: MessagesState) -> dict:
        """
        Cardinal node: injects the system prompt and calls the LLM.

        The system prompt is not saved in the state (too redundant);
        it is prepended to the messages for each call.
        """

        messages = [SystemMessage(content = CARDINAL_SYSTEM_PROMPT)] + state["messages"]
        response = llm_with_tools.invoke(messages)

        return {"messages": [response]}
    # #enddef cardinal_node

    # LangGraph's ToolNode automatically executes all tool_calls
    # present in the latest AIMessage and adds the ToolMessages to the state
    tool_node = ToolNode(tools)

    graph = StateGraph(MessagesState)
    graph.add_node("cardinal", cardinal_node)
    graph.add_node("tools"   , tool_node)

    graph.add_edge(START, "cardinal")

    # tools_condition reads the last message:
    #   → "tools"   if it contains tool_calls
    #   → END       if it is a direct response
    graph.add_conditional_edges("cardinal", tools_condition)

    # After each tool execution, the flow returns to the cardinal node
    # to process the result and decide the next step
    graph.add_edge("tools", "cardinal")

    memory   : MemorySaver = MemorySaver()
    compiled               = graph.compile(checkpointer = memory)

    tool_names: list[str] = [tool.name for tool in tools]
    logger.info("Agent compilato - tool attivi: %s", tool_names)

    return compiled
# #enddef build_agent
