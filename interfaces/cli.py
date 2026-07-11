"""
interface/cli.py - Cardinal's cli powered by Rich

Starts an interactive conversation loop in the terminal.
Every session has a fixed thread_id so the memory MemorySaver
keeps the memory for all the session
"""

import uuid
import logging

# rich import
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text

from langchain_core.messages import HumanMessage

logger  = logging.getLogger(__name__)
console = Console()

def run_cli(agent) -> None:
    """
    CLI runner loop

    Args:
        agent: CompiledStateGraph returned by the build_agent()
    """

    thread_id : str  = str(uuid.uuid4())
    config    : dict = {"configurable": {"thread_id": thread_id}}

    console.print(
        Panel(
            Text("C A R D I N A L", justify="center", style="bold white"),
            subtitle="[dim]Scrivi [bold]exit[/bold] o [bold]quit[/bold] per uscire[/dim]",
            border_style="bright_blue",
            padding=(1, 4),
        )
    )

    console.print()

    # NOTE: maybe remove while True
    while True:

        try:
            user_input = Prompt.ask("[bold cyan]Tu[/bold cyan]")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Sessione terminata.[/dim]")
            break
        # #endtry

        if (user_input.strip().lower() in {"exit", "quit", "esci"}):
            console.print("[dim]Sessione terminata.[/dim]")
            break
        # #endif

        if (not user_input.strip()):
            continue
        # #endif

        # Elaborate the message
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

        # Extract the last message sent by the AI
        last_message = result["messages"][-1]
        content = last_message.content
        if isinstance(content, list):
            response_text = " ".join(
                block.get("text", "") if isinstance(block, dict) else str(block)
                for block in content
            ).strip()
        else:
            response_text = content
        # #endif

        # Shows the response as Markdown in a specific Panel
        console.print()

        console.print(
            Panel(
                Markdown(response_text),
                title="[bold bright_blue]Cardinal[/bold bright_blue]",
                border_style="bright_blue",
                padding=(0, 2),
            )
        )

        console.print()
    # #endwhile
# #enddef run_cli
