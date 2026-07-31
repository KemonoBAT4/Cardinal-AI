"""
interfaces/cli.py  —  CLI di Cardinal con Rich

Usa la sessione persistente (THREAD_ID fisso) invece di un uuid casuale,
così Cardinal ricorda la conversazione tra riavvii.
Dopo ogni risposta estrae fatti rilevanti nella long-term memory.
"""
import logging

from langchain_core.messages import HumanMessage
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text

from memory.short_term import get_session_config

logger = logging.getLogger(__name__)
console = Console()


def run_cli(agent, memory_manager=None, llm=None) -> None:
    """
    Loop principale della CLI.

    Args:
        agent:          CompiledStateGraph da build_agent()
        memory_manager: MemoryManager per estrarre memorie dopo ogni turno
        llm:            BaseChatModel nudo (senza tool) per l'estrazione memorie
    """
    config = get_session_config()  # thread_id fisso e persistente

    # ── Banner ────────────────────────────────────────────────────────────────
    console.print(Panel(
        Text("C A R D I N A L", justify="center", style="bold white"),
        subtitle="[dim]Scrivi [bold]exit[/bold] per uscire[/dim]",
        border_style="bright_blue",
        padding=(1, 4),
    ))

    # Mostra quante memorie sono disponibili
    if memory_manager:
        n = memory_manager.long_term.count()
        if n > 0:
            console.print(f"[dim]  {n} memorie a lungo termine disponibili.[/dim]\n")
        else:
            console.print("[dim]  Nessuna memoria precedente — prima sessione.[/dim]\n")

    # ── Loop conversazione ────────────────────────────────────────────────────
    while True:
        try:
            user_input = Prompt.ask("[bold cyan]Tu[/bold cyan]")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Sessione terminata.[/dim]")
            break

        if user_input.strip().lower() in {"exit", "quit", "esci"}:
            console.print("[dim]Sessione terminata.[/dim]")
            break

        if not user_input.strip():
            continue

        with console.status("[dim]Cardinal sta elaborando...[/dim]", spinner="dots"):
            try:
                result = agent.invoke(
                    {"messages": [HumanMessage(content=user_input)]},
                    config=config,
                )
            except Exception as e:
                logger.exception("Errore durante l'invocazione dell'agent")
                console.print(f"[bold red]Errore:[/bold red] {e}")
                continue

        # Estrai il testo dalla risposta (stringa o lista di blocchi)
        last_message = result["messages"][-1]
        content = last_message.content
        if isinstance(content, list):
            response_text = " ".join(
                block.get("text", "") if isinstance(block, dict) else str(block)
                for block in content
            ).strip()
        else:
            response_text = content

        # Mostra la risposta
        console.print()
        console.print(Panel(
            Markdown(response_text),
            title="[bold bright_blue]Cardinal[/bold bright_blue]",
            border_style="bright_blue",
            padding=(0, 2),
        ))
        console.print()

        # Estrai e salva fatti rilevanti in background
        if memory_manager and llm:
            memory_manager.extract_and_store(user_input, response_text, llm)