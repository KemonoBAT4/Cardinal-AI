cardinal/
├── main.py                    # Entry point (CLI/API/Voice mode)
├── .env
├── config/
│   └── settings.py            # Pydantic BaseSettings
├── core/
│   ├── agent.py               # LangGraph StateGraph principale
│   ├── planner.py             # Task decomposition
│   ├── personality.py         # System prompt + persona Cardinal
│   └── context.py             # Context window management
├── interfaces/
│   ├── voice/
│   │   ├── stt.py             # Faster-Whisper
│   │   ├── tts.py             # Coqui TTS / ElevenLabs
│   │   └── wake_word.py       # Porcupine (riuso da Midnight)
│   ├── api/
│   │   ├── server.py          # FastAPI app
│   │   ├── routes/
│   │   └── ws.py              # WebSocket handler
│   └── cli.py                 # Rich CLI
├── memory/
│   ├── short_term.py          # ConversationBuffer (Redis)
│   ├── long_term.py           # ChromaDB / Qdrant
│   └── episodic.py            # SQLAlchemy + SQLite
├── knowledge/
│   ├── indexer.py             # Ingest documenti → embedding
│   ├── retriever.py           # RAG retrieval
│   └── embeddings.py          # sentence-transformers
├── tools/
│   ├── base.py                # BaseTool ABC
│   ├── web_search.py          # Tavily API
│   ├── file_manager.py
│   ├── code_executor.py       # Sandbox RestrictedPython
│   ├── calendar_tool.py
│   └── notifications.py       # plyer / notify2
└── utils/
    ├── logger.py
    └── helpers.py