"""
core/agent.py  —  Cardinal Agent Core

Flusso del grafo:

  START
    │
    ▼
  cardinal_node  ──► (ha tool_calls?)  ──► tools_node
    ▲                      │ no                │
    │                      ▼                  │
    │                     END                 │
    └─────────────────────────────────────────┘

Novità rispetto alla versione base:
  - accetta un checkpointer esterno (SqliteSaver) per persistenza su disco
  - inietta memorie semantiche rilevanti nel system prompt prima di ogni risposta
"""
import logging
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from config.settings import Settings
from core.llm import LLMBackend
from core.personality import CARDINAL_SYSTEM_PROMPT
from tools.base import get_tools

logger = logging.getLogger(__name__)


def build_agent(
    settings: Settings,
    backend: Optional[LLMBackend] = None,
    memory_manager=None,
    checkpointer=None,
):
    """
    Costruisce e compila il grafo LangGraph di Cardinal.

    Args:
        settings:        configurazione dal .env
        backend:         LLMBackend (se None ne crea uno nuovo)
        memory_manager:  MemoryManager per iniezione memoria semantica
        checkpointer:    SqliteSaver per persistenza (se None usa MemorySaver)
    """
    if backend is None:
        backend = LLMBackend(settings)

    tools = get_tools()
    llm_with_tools = backend.with_tools(tools)

    # ── Nodi ──────────────────────────────────────────────────────────────────

    def cardinal_node(state: MessagesState) -> dict:
        # Trova l'ultimo messaggio dell'utente per la ricerca in memoria
        last_human = next(
            (m for m in reversed(state["messages"]) if isinstance(m, HumanMessage)),
            None,
        )

        # Costruisce il system prompt con le memorie rilevanti iniettate
        system_content = CARDINAL_SYSTEM_PROMPT
        if memory_manager and last_human:
            memory_context = memory_manager.get_context(last_human.content)
            if memory_context:
                system_content += f"\n\n{memory_context}"

        messages = [SystemMessage(content=system_content)] + state["messages"]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    tool_node = ToolNode(tools)

    # ── Grafo ─────────────────────────────────────────────────────────────────

    graph = StateGraph(MessagesState)
    graph.add_node("cardinal", cardinal_node)
    graph.add_node("tools", tool_node)
    graph.add_edge(START, "cardinal")
    graph.add_conditional_edges("cardinal", tools_condition)
    graph.add_edge("tools", "cardinal")

    # Usa SqliteSaver se fornito, altrimenti fallback su MemorySaver in-RAM
    if checkpointer is None:
        from langgraph.checkpoint.memory import MemorySaver
        checkpointer = MemorySaver()
        logger.warning("Checkpointer non fornito — uso MemorySaver (non persistente)")

    compiled = graph.compile(checkpointer=checkpointer)
    logger.info("Agent compilato — tool: %s", [t.name for t in tools])
    return compiled