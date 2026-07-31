"""
core/agent.py  —  Cardinal Agent Core

Graphs' flow:

  START
    │
    ▼
  cardinal_node  ──► (hsa tool_calls?)  ──► tools_node
    ▲                      │ no                │
    │                      ▼                   │
    │                     END                  │
    └──────────────────────────────────────────┘

- Accpets an external checkpointer (SqliteSaver) for persistent memory
- Injects semantic memories relevant in the system prompt before each response
"""

import logging
import typing

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

from config.settings import Settings
from core.llm import LLMBackend
from core.personality import CARDINAL_SYSTEM_PROMPT
from tools.base import get_tools

logger = logging.getLogger(__name__)


def build_agent(
    settings       : Settings,
    backend        : typing.Optional[LLMBackend] = None,
    memory_manager : typing.Any | None           = None,
    checkpointer   : typing.Any | None           = None,
):
    """
    Builds and compiles the Cardinal LangGraph graph.

    Args:
        settings:        configurazione dal .env
        backend:         LLMBackend (se None ne crea uno nuovo)
        memory_manager:  MemoryManager dedicated for injecting semantic memory
        checkpointer:    SqliteSaver for persistency, if None uses MemorySaver
    """

    if backend is None:
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

        # finds the last message sent by the user for memory injection
        last_human = next(
            (
                m for m in reversed(state["messages"]) if isinstance(m, HumanMessage)
            ),
            None,
        )

        # builds the system prompt with relevant memories
        system_content = CARDINAL_SYSTEM_PROMPT
        if memory_manager and last_human:
            memory_context = memory_manager.get_context(last_human.content)

            if memory_context:
                system_content += f"\n\n{memory_context}"
            # #endif
        # #endif

        messages = [SystemMessage(content=system_content)] + state["messages"]
        response = llm_with_tools.invoke(messages)

        return {"messages": [response]}
    # #enddef cardinal_node

    # LangGraph's ToolNode automatically executes all tool_calls
    # present in the latest AIMessage and adds the ToolMessages to the state
    tool_node = ToolNode(tools)

    graph = StateGraph(MessagesState)

    graph.add_node("cardinal", cardinal_node)
    graph.add_node("tools", tool_node)

    graph.add_edge(START, "cardinal")

    # tools_condition reads the last message:
    #   → "tools" if it contains tool_calls
    #   → END     if it is a direct response
    graph.add_conditional_edges("cardinal", tools_condition)

    # After each tool execution, the flow returns to the cardinal node
    # to process the result and decide the next step
    graph.add_edge("tools", "cardinal")

    # Uses SqliteSaver if provided, otherwise fallbacks to MemorySaver
    if checkpointer is None:
        checkpointer = MemorySaver()

        logger.warning("Checkpointer non fornito — uso MemorySaver (non persistente)")
    # #endif

    compiled = graph.compile(checkpointer = checkpointer)
    logger.info("Agent compilato — tool: %s", [t.name for t in tools])

    return compiled
# #enddef build_agent
