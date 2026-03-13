"""
Zerith AI — Workflow Engine
Chain multi-step workflows with support for saved and reusable workflows.
"""

import json
from pathlib import Path
from typing import Optional
from utils.logger import log
import config


class Workflow:
    """A saved, reusable workflow template."""

    def __init__(self, name: str, description: str, steps: list[dict]):
        self.name = name
        self.description = description
        self.steps = steps  # List of {"tool": ..., "action": ..., "params": ...}

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "steps": self.steps,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Workflow":
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            steps=data.get("steps", []),
        )


class WorkflowEngine:
    """Manage and execute saved workflows."""

    WORKFLOWS_FILE = config.DATA_DIR / "workflows.json"

    def __init__(self):
        self._workflows: dict[str, Workflow] = {}
        self._load()

    def _load(self):
        """Load saved workflows from disk."""
        if self.WORKFLOWS_FILE.exists():
            try:
                with open(self.WORKFLOWS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for name, wf_data in data.items():
                    self._workflows[name] = Workflow.from_dict(wf_data)
                log.debug(f"Loaded {len(self._workflows)} workflow(s)")
            except (json.JSONDecodeError, IOError) as e:
                log.warning(f"Could not load workflows: {e}")

    def _save(self):
        """Persist workflows to disk."""
        self.WORKFLOWS_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = {name: wf.to_dict() for name, wf in self._workflows.items()}
        with open(self.WORKFLOWS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def create_workflow(self, name: str, description: str, steps: list[dict]) -> str:
        """Create and save a new workflow."""
        wf = Workflow(name=name, description=description, steps=steps)
        self._workflows[name] = wf
        self._save()
        log.info(f"Workflow created: {name} ({len(steps)} steps)")
        return f"Workflow '{name}' created with {len(steps)} steps"

    def get_workflow(self, name: str) -> Optional[Workflow]:
        """Get a saved workflow by name."""
        return self._workflows.get(name)

    def list_workflows(self) -> str:
        """List all saved workflows."""
        if not self._workflows:
            return "No workflows saved"
        lines = []
        for name, wf in self._workflows.items():
            lines.append(f"  📋 {name} — {wf.description} ({len(wf.steps)} steps)")
        return "\n".join(lines)

    def delete_workflow(self, name: str) -> str:
        """Delete a saved workflow."""
        if name in self._workflows:
            del self._workflows[name]
            self._save()
            return f"Workflow '{name}' deleted"
        return f"Workflow '{name}' not found"

    def run_workflow(self, name: str, router, executor) -> Optional[dict]:
        """Run a saved workflow through the executor."""
        wf = self.get_workflow(name)
        if not wf:
            log.warning(f"Workflow not found: {name}")
            return None

        log.info(f"[bold cyan]Running workflow:[/bold cyan] {name}")
        from core.task_planner import TaskPlan, TaskStep

        steps = [
            TaskStep(step=i + 1, tool=s["tool"], action=s["action"], params=s.get("params", {}))
            for i, s in enumerate(wf.steps)
        ]
        plan = TaskPlan(thought=f"Executing workflow: {name}", steps=steps, response="")
        return executor.execute_plan(plan)


# Handler map for router registration
def _list_workflows() -> str:
    return WorkflowEngine().list_workflows()


HANDLERS = {
    "list_workflows": _list_workflows,
}
