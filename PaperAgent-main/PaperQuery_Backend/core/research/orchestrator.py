"""Research Orchestrator：编排 Planner → Executor → Verifier。"""
from __future__ import annotations

import asyncio

from core.research.executor import Executor
from core.research.planner import Planner
from core.research.schemas import TaskState
from core.research.verifier import Verifier


class ResearchOrchestrator:
    def __init__(self, planner: Planner, executor: Executor, verifier: Verifier):
        self.planner = planner
        self.executor = executor
        self.verifier = verifier

    def run(self, goal: str) -> TaskState:
        plan = self.planner.plan(goal)
        step_results = asyncio.run(self.executor.run(plan))

        artifacts: list[dict] = []
        for r in step_results:
            for a in r.output.get("artifacts", []):
                if isinstance(a, dict):
                    artifacts.append(a)

        ok, _checks = self.verifier.verify(plan, step_results, artifacts)
        return TaskState(
            task_id=plan.task_id,
            goal=goal,
            status="SUCCESS" if ok else "FAILED",
            plan=plan,
            step_results=step_results,
            artifacts=artifacts,
        )
