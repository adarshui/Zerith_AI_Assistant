"""
Zerith AI — Task Planner
Breaks user commands into structured, executable task steps.
"""

from typing import Optional
from core.brain import Brain
from utils.logger import log


class TaskStep:
    """Represents a single executable step in a plan."""

    def __init__(self, step: int, tool: str, action: str, params: Optional[dict] = None):
        self.step = step
        self.tool = tool
        self.action = action
        self.params = params or {}
        self.status = "pending"   # pending | running | success | failed
        self.result = None

    def __repr__(self):
        return f"Step {self.step}: [{self.tool}.{self.action}] ({self.status})"

    def to_dict(self) -> dict:
        return {
            "step": self.step,
            "tool": self.tool,
            "action": self.action,
            "params": self.params,
            "status": self.status,
            "result": self.result,
        }


class TaskPlan:
    """A complete plan with multiple steps."""

    def __init__(self, thought: str, steps: list[TaskStep], response: str):
        self.thought = thought
        self.steps = steps
        self.response = response

    @property
    def is_complete(self) -> bool:
        return all(s.status in ("success", "failed") for s in self.steps)

    @property
    def has_failures(self) -> bool:
        return any(s.status == "failed" for s in self.steps)

    def __repr__(self):
        return f"TaskPlan({len(self.steps)} steps, complete={self.is_complete})"


class TaskPlanner:
    """Converts user commands into structured TaskPlans via the LLM."""

    def __init__(self, brain: Brain):
        self.brain = brain

    def plan(self, user_command: str, context: str = "") -> TaskPlan:
        """
        Take a user command and produce a TaskPlan.
        """
        log.info(f"[cyan]Planning:[/cyan] {user_command}")

        result = self.brain.think(user_command, context=context)

        thought = result.get("thought", "")
        response = result.get("response", "")
        raw_steps = result.get("plan", [])

        steps = []
        for i, raw in enumerate(raw_steps):
            step = TaskStep(
                step=raw.get("step", i + 1),
                tool=raw.get("tool", "unknown"),
                action=raw.get("action", "unknown"),
                params=raw.get("params", {}),
            )
            steps.append(step)

        plan = TaskPlan(thought=thought, steps=steps, response=response)
        log.info(f"[green]Plan created:[/green] {len(steps)} step(s)")
        for s in steps:
            log.debug(f"  {s}")

        return plan
