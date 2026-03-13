"""
Zerith AI — Permissions / Safety Layer
Prompts the user for confirmation before critical operations.
"""

from rich.console import Console
from rich.prompt import Confirm
from rich.panel import Panel
from utils.logger import log
import config

console = Console()

# Actions that always require user permission
CRITICAL_ACTIONS = set(config.REQUIRE_CONFIRMATION_FOR)


def requires_permission(action: str) -> bool:
    """Check if an action needs explicit user permission."""
    return action in CRITICAL_ACTIONS


def request_permission(action: str, details: str = "") -> bool:
    """
    Show a warning and ask the user to confirm a critical action.
    Returns True if user approves, False otherwise.
    """
    message = f"[bold red]⚠  CRITICAL ACTION:[/bold red] [yellow]{action}[/yellow]"
    if details:
        message += f"\n   [dim]{details}[/dim]"

    console.print()
    console.print(Panel(message, title="🔒 Permission Required", border_style="red"))

    approved = Confirm.ask("   Do you want to proceed?", default=False)
    if approved:
        log.info(f"Permission GRANTED for: {action}")
    else:
        log.warning(f"Permission DENIED for: {action}")
    return approved


def check_and_confirm(action: str, details: str = "") -> bool:
    """
    Convenience function: returns True immediately if the action is safe,
    or asks for permission if it is critical.
    """
    if not requires_permission(action):
        return True
    return request_permission(action, details)
