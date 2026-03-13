"""
Zerith AI — CLI Interface
Rich-formatted command line interface for interacting with Zerith.
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich import box
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from utils.logger import log
import config

console = Console()


def print_banner():
    """Display the Zerith welcome banner."""
    banner = """
[bold cyan]╔══════════════════════════════════════════╗
║         ⚡  Z E R I T H  A I  ⚡         ║
║      Personal Desktop AI Assistant       ║
╚══════════════════════════════════════════╝[/bold cyan]
"""
    console.print(banner)
    # Show the correct model based on active provider
    model_map = {
        "groq": config.GROQ_MODEL,
        "ollama": config.OLLAMA_MODEL,
        "openai": config.OPENAI_MODEL,
    }
    active_model = model_map.get(config.LLM_PROVIDER, config.LLM_PROVIDER)
    console.print(f"  [dim]Provider: {config.LLM_PROVIDER} | Model: {active_model}[/dim]")
    console.print(f"  [dim]Type 'help' for commands, 'quit' to exit[/dim]")
    console.print()


def print_plan(plan):
    """Display a task plan in a formatted table."""
    table = Table(title="📋 Task Plan", box=box.ROUNDED, show_lines=True)
    table.add_column("#", style="bold cyan", width=4)
    table.add_column("Tool", style="yellow")
    table.add_column("Action", style="green")
    table.add_column("Params", style="dim")
    table.add_column("Status", style="bold")

    for step in plan.steps:
        status_icon = {
            "pending": "⏳",
            "running": "🔄",
            "success": "✅",
            "failed": "❌",
        }.get(step.status, "❓")

        table.add_row(
            str(step.step),
            step.tool,
            step.action,
            str(step.params)[:50] if step.params else "",
            f"{status_icon} {step.status}",
        )

    console.print(table)


def print_results(summary: dict):
    """Display execution results."""
    total = summary["total_steps"]
    ok = summary["success"]
    fail = summary["failed"]
    skipped = total - summary["executed"]

    panel_text = f"✅ Success: {ok}  ❌ Failed: {fail}  ⏭ Skipped: {skipped}"
    style = "green" if fail == 0 else "red"
    console.print(Panel(panel_text, title="Execution Results", border_style=style))


def print_response(text: str):
    """Print an AI response — extract clean text from JSON if needed."""
    import json
    display_text = text
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict) and "response" in parsed:
            display_text = parsed["response"]
    except (json.JSONDecodeError, TypeError):
        pass
    console.print()
    console.print(Panel(Markdown(display_text), title="🤖 Zerith", border_style="cyan"))
    console.print()


def show_help():
    """Display available commands."""
    help_text = """
[bold]Available Commands:[/bold]

  [cyan]help[/cyan]        — Show this help message
  [cyan]quit[/cyan]        — Exit Zerith
  [cyan]clear[/cyan]       — Clear conversation history
  [cyan]status[/cyan]      — Show system status
  [cyan]tools[/cyan]       — List available tools
  [cyan]memory[/cyan]      — Show stored memories
  [cyan]prefs[/cyan]       — Show user preferences
  [cyan]workflows[/cyan]   — List saved workflows
  [cyan]screenshot[/cyan]  — Capture and analyze screen
  [cyan]voice[/cyan]       — Toggle voice mode

  [dim]Or just type a natural language command![/dim]
"""
    console.print(Panel(help_text, title="📖 Help", border_style="blue"))


def create_prompt_session() -> PromptSession:
    """Create a prompt session with history."""
    history_file = config.DATA_DIR / "command_history.txt"
    history_file.parent.mkdir(parents=True, exist_ok=True)
    return PromptSession(history=FileHistory(str(history_file)))
