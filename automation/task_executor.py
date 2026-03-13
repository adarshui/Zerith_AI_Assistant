"""
Zerith AI — Task Executor
Execute individual task steps dispatched by the agent router.
"""

import time
from utils.logger import log


class TaskExecutor:
    """Executes steps from a TaskPlan, handles retries and timing."""

    def __init__(self, router):
        self.router = router
        self.max_retries = 2
        self.step_delay = 0.5  # seconds between steps

    def execute_step(self, step) -> str:
        """Execute a single step with optional retries."""
        attempt = 0
        while attempt <= self.max_retries:
            result = self.router.execute_step(step)
            if step.status == "success":
                return result
            attempt += 1
            if attempt <= self.max_retries:
                log.warning(f"Retrying step {step.step} (attempt {attempt + 1})")
                time.sleep(self.step_delay)

        return step.result or "Step failed after retries"

    def execute_plan(self, plan) -> dict:
        """
        Execute all steps in a plan, collecting results.
        Returns summary dict.
        """
        log.info(f"[bold cyan]Executing plan:[/bold cyan] {len(plan.steps)} step(s)")
        results = []

        for i, step in enumerate(plan.steps):
            log.info(f"[yellow]Step {step.step}/{len(plan.steps)}:[/yellow] {step.tool}.{step.action}")
            result = self.execute_step(step)
            results.append(step.to_dict())

            if step.status == "failed":
                log.warning(f"Plan halted at step {step.step}")
                break

            if i < len(plan.steps) - 1:
                time.sleep(self.step_delay)

        success_count = sum(1 for r in results if r["status"] == "success")
        fail_count = sum(1 for r in results if r["status"] == "failed")

        summary = {
            "total_steps": len(plan.steps),
            "executed": len(results),
            "success": success_count,
            "failed": fail_count,
            "complete": plan.is_complete,
            "results": results,
        }

        log.info(
            f"[bold]Plan result:[/bold] {success_count} success, {fail_count} failed, "
            f"{len(plan.steps) - len(results)} skipped"
        )
        return summary
