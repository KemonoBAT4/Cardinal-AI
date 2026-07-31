"""
interfaces/cli.py - Cardinal's CLI with Rich

Uses the persistent session (fixed THREAD_ID) instead of a random uuid,
so Cardinal remembers the conversation even after restart.
After each response, it extracts relevant facts from the long-term memory.
"""

import logging

from langchain_core.messages import HumanMessage
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text

from memory.short_term import get_session_config
from utils.helpers import extract_text

logger = logging.getLogger(__name__)
console = Console()

def run_cli(agent, memory_manager=None, llm=None) -> None:
    """
    Main CLI loop

    Args:
        agent:          CompiledStateGraph from build_agent()
        memory_manager: MemoryManager to extract memories after each turn
        llm:            BaseChatModel without tools to extract memories
    """

    config = get_session_config()

    console.print(Panel(
        Text("C A R D I N A L", justify = "center", style = "bold white"),
        subtitle     = "[dim]Scrivi [bold]exit[/bold] per uscire[/dim]",
        border_style = "bright_blue",
        padding      = (1, 4),
    ))

    # NOTE: debug only, remove this in production
    if memory_manager:
        n = memory_manager.long_term.count()
        if n > 0:
            console.print(f"[dim]  {n} memorie a lungo termine disponibili.[/dim]\n")
        else:
            console.print("[dim]  Nessuna memoria precedente — prima sessione.[/dim]\n")
        # #endif
    # #endif

    while True:
        try:
            user_input = Prompt.ask("[bold cyan]Tu[/bold cyan]")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Sessione terminata.[/dim]")
            break
        # #endtry

        if user_input.strip().lower() in {"exit", "quit", "esci"}:
            console.print("[dim]Sessione terminata.[/dim]")
            break
        # #endif

        if not user_input.strip():
            continue
        # #endif

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
            # #endtry
        # #endwith

        last_message = result["messages"][-1]
        content = last_message.content

        response_text = extract_text(content)

        console.print()
        console.print(Panel(
            Markdown(response_text),
            title="[bold bright_blue]Cardinal[/bold bright_blue]",
            border_style="bright_blue",
            padding=(0, 2),
        ))
        console.print()

        if memory_manager and llm:
            memory_manager.extract_and_store(user_input, response_text, llm)
        # #endif
    # #endwhile
#enddef run_cli
