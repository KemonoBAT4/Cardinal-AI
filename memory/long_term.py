"""
memory/long_term.py - Semantic long term memory with ChromaDB

Saves all the importants facts extracted from the conversations, (preferences,
user name, projects, ecc... ) and retrieves with semantic similarity

Dependencies : pip install chromadb sentence-transformers
"""
import uuid
from datetime import datetime
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

class LongTermMemory:
    """
    Vector store persistente per la memoria semantica di Cardinal.

    Ogni memoria è un testo breve con metadati (timestamp, tipo, sessione).
    La ricerca avviene per similarità semantica tramite sentence-transformers.
    """

    def __init__(self, persist_dir: str = "./data/chroma") -> None:
        Path(persist_dir).mkdir(parents=True, exist_ok=True)

        self._client = chromadb.PersistentClient(path=persist_dir)
        self._ef = SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"  # modello leggero, ~80MB, buona qualità
        )
        self._collection = self._client.get_or_create_collection(
            name="cardinal_memories",
            embedding_function=self._ef,
        )

    # ── Scrittura ─────────────────────────────────────────────────────────────

    def store(self, text: str, memory_type: str = "fact") -> None:
        """
        Salva una memoria nella vector store.

        Args:
            text:        contenuto della memoria
                         es. "L'utente si chiama Marco e lavora come developer"
            memory_type: categoria — 'fact', 'preference', 'event', 'summary'
        """
        self._collection.add(
            documents=[text],
            metadatas=[{
                "timestamp": datetime.now().isoformat(),
                "type": memory_type,
            }],
            ids=[str(uuid.uuid4())],
        )

    # ── Lettura ───────────────────────────────────────────────────────────────

    def search(self, query: str, k: int = 5) -> list[str]:
        """
        Cerca le k memorie più rilevanti per la query.

        Returns:
            Lista di stringhe ordinate per rilevanza semantica.
        """
        count = self._collection.count()

        if count == 0:
            return []
        # #endif

        results = self._collection.query(
            query_texts = [query],
            n_results   = min(k, count),
        )

        return results["documents"][0] if results["documents"] else []
    # #enddef search

    def count(self) -> int:
        """Number of saved memories"""
        return self._collection.count()
    # #enddef count
# #endclass 