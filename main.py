"""
main.py -> Cardinal's entry point

Use:
    python main.py              # starts the CLI (default)
    python main.py --mode cli
"""

from dotenv import load_dotenv
load_dotenv()

import argparse
import logging

from config.settings import Settings
from core.agent import build_agent
from core.llm import LLMBackend


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Cardinal AI Assistant")
    parser.add_argument(
        "--mode",
        choices=["cli", "api", "voice"],
        default="cli",
        help="Modalità di avvio (default: cli)",
    )
    args = parser.parse_args()

    # loads the configuration from the .env
    settings = Settings()

    # init the LLM backend (Claude + fallback Ollama)
    backend = LLMBackend(settings)

    # compiles the agent LangGraph
    agent = build_agent(settings, backend)

    if args.mode == "cli":
        from interfaces.cli import run_cli
        run_cli(agent)

    elif args.mode == "api":
        # NOTE: Not implemented yet, need to be implemented with FastAPI
        raise NotImplementedError("Modalità API non ancora implementata.")

    elif args.mode == "voice":
        # NOTE: Not implemented yet, need to be implemented with Porcupine + Whisper
        raise NotImplementedError("Modalità Voice non ancora implementata.")
    # #endif
# #enddef main

if __name__ == "__main__":
    main()
# #endif
