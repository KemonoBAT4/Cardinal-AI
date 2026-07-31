"""
memory/short_term.py - Session's Persistency with SqliteSaver

Replaces MemorySaver (RAM) with SqliteSaver (on db).
fixed THREAD_ID = unique conversation that continues even after the application restarts

Dependeciy : pip install langgraph-checkpoint-sqlite
"""

import sqlite3
from pathlib import Path
 
from langgraph.checkpoint.sqlite import SqliteSaver

# Unique persistent thread - every conversation made with cardinal
THREAD_ID = "cardinal-main"
  
def get_checkpointer(db_path: str = "./data/cardinal_memory.db") -> SqliteSaver:
    """
    Creates and returns the SQLite checkpointer
    - Automatically create the folder data/
    Crea automaticamente la cartella data/ se non esiste.
    """
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    return SqliteSaver(conn)
# #enddef get_checkpointer
 
def get_session_config() -> dict:
    """
    The configuration that has to be passed to the agent.invoke()
    and agent.stream().

    Identifies Cardinal's the persistent session
    """
    return {"configurable": {"thread_id": THREAD_ID}}
# #enddef get_session_config
