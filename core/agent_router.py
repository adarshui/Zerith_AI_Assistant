"""
Zerith AI — Agent Router
Routes planned task steps to the correct tool module and executes them.
"""

from typing import Callable
from core.task_planner import TaskPlan, TaskStep
from utils.logger import log
from utils.permissions import check_and_confirm


class AgentRouter:
    """
    Central dispatcher — maps tool names to handler functions
    and executes task plans step by step.
    """

    def __init__(self):
        # Registry: tool_name -> { action_name -> callable }
        self._tools: dict[str, dict[str, Callable]] = {}

    # ── Tool Registration ────────────────────────────────

    def register_tool(self, tool_name: str, action_name: str, handler: Callable):
        """Register a handler function for tool_name.action_name."""
        if tool_name not in self._tools:
            self._tools[tool_name] = {}
        self._tools[tool_name][action_name] = handler
        log.debug(f"Registered tool: {tool_name}.{action_name}")

    def register_module(self, tool_name: str, handlers: dict[str, Callable]):
        """Register multiple actions for a tool at once."""
        for action, handler in handlers.items():
            self.register_tool(tool_name, action, handler)

    # ── Execution ────────────────────────────────────────

    def execute_step(self, step: TaskStep) -> str:
        """Execute a single task step and return the result."""
        tool = step.tool
        action = step.action
        params = step.params

        log.info(f"[yellow]Executing:[/yellow] {tool}.{action} {params}")
        step.status = "running"

        # Safety check for critical actions
        critical_key = f"{tool}_{action}" if tool != "system" else action
        if tool == "system" or action in ("delete_file", "delete_folder"):
            detail = f"{tool}.{action}({params})"
            if not check_and_confirm(critical_key, detail):
                step.status = "failed"
                step.result = "User denied permission"
                return step.result

        # Look up handler
        if tool not in self._tools:
            step.status = "failed"
            step.result = f"Unknown tool: {tool}"
            log.warning(step.result)
            return step.result

        if action not in self._tools[tool]:
            step.status = "failed"
            step.result = f"Unknown action: {tool}.{action}"
            log.warning(step.result)
            return step.result

        handler = self._tools[tool][action]

        try:
            result = handler(**params)
            step.status = "success"
            step.result = str(result) if result is not None else "Done"
            log.info(f"[green]✓[/green] {tool}.{action} completed")
            return step.result
        except Exception as e:
            step.status = "failed"
            step.result = f"Error: {e}"
            log.warning(f"[red]✗[/red] {tool}.{action} failed: {e}")
            return step.result

    def execute_plan(self, plan: TaskPlan) -> list[dict]:
        """Execute all steps in a plan sequentially. Returns list of results."""
        results = []
        for step in plan.steps:
            result = self.execute_step(step)
            results.append(step.to_dict())

            # Stop on failure (can be made configurable)
            if step.status == "failed":
                log.warning(f"Plan halted at step {step.step} due to failure.")
                break

        return results

    @property
    def available_tools(self) -> dict[str, list[str]]:
        """Return a summary of all registered tools and their actions."""
        return {tool: list(actions.keys()) for tool, actions in self._tools.items()}
