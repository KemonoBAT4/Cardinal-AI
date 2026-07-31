"""
memory/long_term.py  —  Memoria semantica a lungo termine con ChromaDB

Salva fatti importanti estratti dalle conversazioni (preferenze, nome
dell'utente, progetti, ecc.) e li recupera per similarità semantica.

Il modello sentence-transformers viene caricato in lazy loading:
solo al primo store() o search(), non all'avvio dell'app.

Dipendenze: pip install chromadb sentence-transformers
"""
import uuid
from datetime import datetime
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction


class LongTermMemory:
    """
    Vector store persistente per la memoria semantica di Cardinal.

    Ogni memoria è un testo breve con metadati (timestamp, tipo).
    La ricerca avviene per similarità semantica tramite sentence-transformers.
    Il modello viene caricato solo al primo utilizzo reale.
    """

    def __init__(self, persist_dir: str = "./data/chroma") -> None:
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=persist_dir)
        # Lazy: nessun caricamento modello finché non serve davvero
        self._ef = None
        self._collection = None

    def _get_collection(self):
        """
        Inizializza embedding model e collection solo al primo utilizzo.
        Dopo la prima chiamata ritorna direttamente l'istanza già pronta.
        """
        if self._collection is None:
            self._ef = SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
            self._collection = self._client.get_or_create_collection(
                name="cardinal_memories",
                embedding_function=self._ef,
            )
        return self._collection

    # ── Scrittura ─────────────────────────────────────────────────────────────

    def store(self, text: str, memory_type: str = "fact") -> None:
        """
        Salva una memoria nella vector store.

        Args:
            text:        contenuto della memoria
                         es. "L'utente lavora su un progetto chiamato Cardinal"
            memory_type: categoria — 'fact', 'preference', 'event', 'summary'
        """
        self._get_collection().add(
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
        Ritorna lista vuota senza caricare il modello se non ci sono memorie.
        """
        # Controllo rapido senza inizializzare il modello
        try:
            existing = self._client.get_collection("cardinal_memories")
            if existing.count() == 0:
                return []
        except Exception:
            return []  # collection non esiste ancora

        results = self._get_collection().query(
            query_texts=[query],
            n_results=min(k, self._get_collection().count()),
        )
        return results["documents"][0] if results["documents"] else []

    def count(self) -> int:
        """Numero di memorie salvate, senza caricare il modello."""
        try:
            return self._client.get_collection("cardinal_memories").count()
        except Exception:
            return 0