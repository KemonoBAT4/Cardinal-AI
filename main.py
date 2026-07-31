"""
main.py  —  Cardinal's entry point

Use case:
    python main.py           # starts the cli (default)
    python main.py --mode cli
"""

import argparse
import logging

from dotenv import load_dotenv

load_dotenv()

from config.settings import Settings
from core.agent import build_agent
from core.llm import LLMBackend
from memory.long_term import LongTermMemory
from memory.manager import MemoryManager
from memory.short_term import get_checkpointer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Cardinal AI Assistant")
    parser.add_argument(
        "--mode",
        choices = ["cli", "api", "voice"],
        default = "cli",
    )
    args = parser.parse_args()

    settings = Settings()

    backend = LLMBackend(settings)

    checkpointer = get_checkpointer(settings.sqllite_path)   # SqliteSaver
    long_term    = LongTermMemory(settings.chroma_persist_dir)
    memory_mgr   = MemoryManager(long_term)

    agent = build_agent(
        settings,
        backend        = backend,
        memory_manager = memory_mgr,
        checkpointer   = checkpointer,
    )

    if args.mode == "cli":
        from interfaces.cli import run_cli
        run_cli(agent, memory_manager=memory_mgr, llm=backend.llm)

    elif args.mode == "api":
        raise NotImplementedError("Modalità API non ancora implementata.")

    elif args.mode == "voice":
        raise NotImplementedError("Modalità Voice non ancora implementata.")
    # #endif
# #enddef main

if __name__ == "__main__":
    main()
# #endif