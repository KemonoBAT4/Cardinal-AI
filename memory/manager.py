"""
memory/manager.py - Coordinates the memory of Cardinal.

Responsabilities:
  1. get_context(query)           -> retrieves the relevant memories before each response
  2. extract_and_store(h, a, llm) -> extract new memories from the conversation
"""

import logging

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage
from memory.long_term import LongTermMemory
from utils.helpers import extract_text  

logger = logging.getLogger(__name__)

# prompt used to extract facts from the conversation
_EXTRACTION_PROMPT = """\
Analizza questo scambio e identifica i fatti importanti sull'utente \
che vale la pena ricordare a lungo termine.

Salva solo informazioni concrete:
- Nome, lavoro, città dell'utente
- Preferenze esplicite ("mi piace X", "non voglio Y")
- Progetti o obiettivi menzionati
- Informazioni tecniche rilevanti (linguaggi, tool, stack)

NON salvare:
- Saluti generici o conversazione banale
- Domande sull'ora o sul meteo
- Cose già ovvie o non relative all'utente

Scambio:
UTENTE: {human}
CARDINAL: {ai}

Rispondi SOLO con una lista di fatti brevi (uno per riga).
Se non ci sono fatti rilevanti scrivi esattamente: NESSUNO
"""

# messages that are too short or trivial to analyze
_TRIVIAL = {"come va", "ciao", "grazie", "ok", "bene", "perfetto", "esci", "quit"}

class MemoryManager:

    long_term: LongTermMemory

    def __init__(self, long_term: LongTermMemory) -> None:
        self.long_term = long_term
    # #enddef __init__

    def get_context(self, query: str) -> str:
        """
        Retrieves the relevant memories and formats them for the system prompt.
        Returns an empty string if no relevant memories are found.
        """

        memories = self.long_term.search(query, k=5)

        if not memories:
            return ""
        # #endif

        lines = "\n".join(f"- {m}" for m in memories)

        return f"MEMORIE SULL'UTENTE:\n{lines}"
    # #enddef get_context

    def extract_and_store(
        self,
        human_msg : str,
        ai_msg    : str,
        llm       : BaseChatModel,
    ) -> None:
        """
        Extracts the relevant facts from the conversation and stores them in the long-term memory.
        """

        if any(k in human_msg.lower() for k in _TRIVIAL):
            return
        # #endif

        try:
            prompt   : str       = _EXTRACTION_PROMPT.format(human=human_msg, ai=ai_msg)
            response : AIMessage = llm.invoke(prompt)

            content: str = extract_text(response)

            if "NESSUNO" in content.upper():
                return
            # #endif

            facts = [
                line.lstrip("- •").strip()
                for line in content.strip().splitlines()
                if line.strip() and len(line.strip()) > 10
            ]

            for fact in facts:
                self.long_term.store(fact, memory_type="fact")
                logger.debug("Memoria salvata: %s", fact)
            # #endfor
        except Exception as e:
            logger.warning("Errore estrazione memoria: %s", e)
        # #endtry
    # #enddef extract_and_store
# #endclass MemoryManager
