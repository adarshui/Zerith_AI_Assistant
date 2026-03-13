"""
Zerith AI — Chat Interface
Interactive chat-style UI using rich.
Wraps the CLI with a more conversational experience.
"""

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from ui.cli_interface import print_banner, print_plan, print_results, print_response

console = Console()


def print_user_message(text: str):
    """Display user message in chat style."""
    console.print(Panel(text, title="👤 You", border_style="bright_white"))


def print_thinking():
    """Show thinking indicator."""
    console.print("  [dim italic]🧠 Thinking...[/dim italic]")


def print_executing():
    """Show executing indicator."""
    console.print("  [dim italic]⚙️  Executing plan...[/dim italic]")


def print_step_progress(step_num: int, total: int, tool: str, action: str):
    """Show progress of current step."""
    console.print(
        f"  [yellow]Step {step_num}/{total}:[/yellow] "
        f"[green]{tool}.{action}[/green]"
    )


def print_error(message: str):
    """Display an error message."""
    console.print(Panel(f"[red]{message}[/red]", title="⚠ Error", border_style="red"))


def print_info(message: str):
    """Display an info message."""
    console.print(f"  [dim]ℹ {message}[/dim]")
