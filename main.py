"""
Zerith AI — Main Entry Point
Initializes all modules, registers tools, and starts the interactive CLI.
"""

import sys
import os

# Ensure project root is on PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from utils.logger import log
from core.brain import Brain
from core.task_planner import TaskPlanner
from core.agent_router import AgentRouter
from automation.task_executor import TaskExecutor
from automation.workflow_engine import WorkflowEngine
from ui.cli_interface import (
    print_banner, print_plan, print_results,
    print_response, show_help, create_prompt_session, console,
)
from ui.chat_interface import (
    print_user_message, print_thinking, print_executing,
    print_step_progress, print_error, print_info,
)


def register_all_tools(router: AgentRouter):
    """Register every tool module with the agent router."""

    # ── Control tools ────────────────────────────────────
    from control.keyboard_control import HANDLERS as kb_handlers
    router.register_module("keyboard", kb_handlers)

    from control.mouse_control import HANDLERS as mouse_handlers
    router.register_module("mouse", mouse_handlers)

    from control.system_commands import HANDLERS as sys_handlers
    router.register_module("system", sys_handlers)

    # ── Vision tools ─────────────────────────────────────
    if config.ENABLE_VISION:
        from vision.screen_capture import HANDLERS as cap_handlers
        router.register_module("vision", cap_handlers)

        from vision.screen_analyzer import HANDLERS as sa_handlers
        router.register_module("vision", sa_handlers)  # adds to existing

        from vision.ocr_reader import HANDLERS as ocr_handlers
        router.register_module("vision", ocr_handlers)  # adds to existing

    # ── Web tools ────────────────────────────────────────
    if config.ENABLE_WEB:
        from web.web_search import HANDLERS as ws_handlers
        router.register_module("web", ws_handlers)

        from web.scraper import HANDLERS as scraper_handlers
        router.register_module("web", scraper_handlers)

        from web.content_extractor import HANDLERS as ce_handlers
        router.register_module("web", ce_handlers)

    # ── Memory tools ─────────────────────────────────────
    from memory.memory_store import HANDLERS as mem_handlers
    router.register_module("memory", mem_handlers)

    from memory.vector_memory import HANDLERS as vec_handlers
    router.register_module("memory", vec_handlers)

    from memory.user_preferences import HANDLERS as pref_handlers
    router.register_module("preferences", pref_handlers)

    # ── File tools ───────────────────────────────────────
    from control.file_operations import HANDLERS as file_handlers
    router.register_module("file", file_handlers)

    # ── Automation ───────────────────────────────────────
    from automation.workflow_engine import HANDLERS as wf_handlers
    router.register_module("automation", wf_handlers)

    log.info(f"[green]✓ Registered {sum(len(v) for v in router.available_tools.values())} tool actions[/green]")


def handle_builtin_command(cmd: str, brain: Brain, router: AgentRouter, workflow_engine: WorkflowEngine) -> bool:
    """
    Handle special built-in commands.
    Returns True if the command was handled, False to pass to AI.
    """
    cmd_lower = cmd.strip().lower()

    if cmd_lower in ("quit", "exit", "bye"):
        console.print("\n[cyan]Goodbye! 👋[/cyan]\n")
        sys.exit(0)

    if cmd_lower == "help":
        show_help()
        return True

    if cmd_lower == "clear":
        brain.reset_history()
        console.print("[dim]Conversation cleared.[/dim]")
        return True

    if cmd_lower == "tools":
        tools = router.available_tools
        for tool_name, actions in sorted(tools.items()):
            console.print(f"  [yellow]{tool_name}[/yellow]: {', '.join(actions)}")
        return True

    if cmd_lower == "status":
        model_map = {
            "groq": config.GROQ_MODEL,
            "ollama": config.OLLAMA_MODEL,
            "openai": config.OPENAI_MODEL,
        }
        active_model = model_map.get(config.LLM_PROVIDER, config.LLM_PROVIDER)
        console.print(f"  Provider: [cyan]{config.LLM_PROVIDER}[/cyan]")
        console.print(f"  Model: [cyan]{active_model}[/cyan]")
        console.print(f"  Vision: {'✅' if config.ENABLE_VISION else '❌'}")
        console.print(f"  Web: {'✅' if config.ENABLE_WEB else '❌'}")
        console.print(f"  Voice: {'✅' if config.ENABLE_VOICE else '❌'}")
        return True

    if cmd_lower == "memory":
        from memory.memory_store import list_memories
        console.print(list_memories())
        return True

    if cmd_lower == "prefs":
        from memory.user_preferences import list_prefs
        console.print(list_prefs())
        return True

    if cmd_lower == "workflows":
        console.print(workflow_engine.list_workflows())
        return True

    if cmd_lower == "screenshot":
        from vision.screen_capture import capture_screen
        path = capture_screen()
        console.print(f"[green]Screenshot saved:[/green] {path}")
        return True

    return False


def main():
    """Main application loop."""
    print_banner()

    # ── Initialize modules ───────────────────────────────
    log.info("Initializing Zerith AI...")

    brain = Brain()
    planner = TaskPlanner(brain)
    router = AgentRouter()
    executor = TaskExecutor(router)
    workflow_engine = WorkflowEngine()

    register_all_tools(router)

    # ── Start CLI loop ───────────────────────────────────
    session = create_prompt_session()
    log.info("[bold green]Zerith AI is ready![/bold green]")
    console.print()

    while True:
        try:
            user_input = session.prompt("⚡ Zerith > ").strip()
            if not user_input:
                continue

            # Check for built-in commands
            if handle_builtin_command(user_input, brain, router, workflow_engine):
                continue

            # ── Process with AI ──────────────────────────
            print_user_message(user_input)
            print_thinking()

            plan = planner.plan(user_input)

            if plan.steps:
                # Show the plan
                print_plan(plan)

                # Ask before executing
                from rich.prompt import Confirm
                if Confirm.ask("  Execute this plan?", default=True):
                    print_executing()

                    for step in plan.steps:
                        print_step_progress(step.step, len(plan.steps), step.tool, step.action)

                    summary = executor.execute_plan(plan)
                    print_results(summary)

                    # Show updated plan with statuses
                    print_plan(plan)
                else:
                    print_info("Plan cancelled.")
            else:
                # No plan — just a conversational response
                print_response(plan.response)

            # Track usage pattern
            from memory.user_preferences import _get_prefs
            _get_prefs().record_pattern("commands", user_input)

        except KeyboardInterrupt:
            console.print("\n[dim]Use 'quit' to exit[/dim]")
            continue
        except EOFError:
            console.print("\n[cyan]Goodbye! 👋[/cyan]\n")
            break


if __name__ == "__main__":
    if "--ui" in sys.argv:
        from web_ui import start_web_ui
        start_web_ui()
    else:
        main()
