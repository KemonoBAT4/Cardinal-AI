"""
memory/manager.py  —  Coordinatore del sistema di memoria di Cardinal

Due responsabilità:
  1. get_context(query)          → recupera memorie rilevanti prima della risposta
  2. extract_and_store(h, a, llm) → estrae nuovi fatti dopo ogni scambio
"""
import logging

from langchain_core.language_models import BaseChatModel
from memory.long_term import LongTermMemory

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
    def __init__(self, long_term: LongTermMemory) -> None:
        self.long_term = long_term
    # #enddef __init__

    def get_context(self, query: str) -> str:
        """
        Recupera le memorie rilevanti e le formatta per il system prompt.
        Ritorna stringa vuota se non ci sono memorie pertinenti.
        """
        memories = self.long_term.search(query, k=5)

        if not memories:
            return ""
        # #endif

        lines = "\n".join(f"- {m}" for m in memories)

        return f"MEMORIE SULL'UTENTE:\n{lines}"
    # #enddef get_context

    def extract_and_store(
        self, human_msg: str, ai_msg: str, llm: BaseChatModel
    ) -> None:
        """
        Estrae fatti rilevanti dallo scambio e li salva nella long-term memory.
        Salta automaticamente conversazione banale per non sprecare chiamate API.
        """
        # Salta se il messaggio è troppo corto o banale
        if len(human_msg.strip()) < 10:
            return
        # #endif

        if any(k in human_msg.lower() for k in _TRIVIAL):
            return
        # #endif

        try:
            prompt = _EXTRACTION_PROMPT.format(human=human_msg, ai=ai_msg)
            response = llm.invoke(prompt)
            raw = response.content if hasattr(response, "content") else response
            if isinstance(raw, list):
                content = " ".join(
                    block.get("text", "") if isinstance(block, dict) else str(block)
                    for block in raw
                ).strip()
            else:
                content = str(raw)
            # #endif

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
