"""Research Executor：顺序执行计划中的步骤。"""
from __future__ import annotations

import time

from core.research.schemas import StepResult, TaskPlan
from core.skills.registry import SkillRegistry


class Executor:
    def __init__(self, registry: SkillRegistry, ctx: dict | None = None):
        self.registry = registry
        self.ctx = ctx or {}

    async def run(self, plan: TaskPlan) -> list[StepResult]:
        results: list[StepResult] = []
        step_outputs: dict[str, dict] = {}

        for step in plan.steps:
            skill = self.registry.get(step.skill)
            skill_input = dict(step.input)
            # 把前置步骤输出注入，供后续步骤引用
            if step.depends_on:
                skill_input["_previous_outputs"] = {
                    dep: step_outputs.get(dep) for dep in step.depends_on
                }

            start = time.time()
            result = await skill.run(skill_input, self.ctx)
            duration_ms = int((time.time() - start) * 1000)
            status = "SUCCESS" if result.ok else "FAILED"
            if result.error_code == "NEED_MORE_EVIDENCE":
                status = "NEED_MORE_EVIDENCE"

            step_result = StepResult(
                step_id=step.step_id,
                status=status,  # type: ignore[arg-type]
                output={**result.output, "artifacts": result.artifacts},
                evidence_ids=result.evidence,
                error=result.error_message,
                duration_ms=duration_ms,
            )
            step_outputs[step.step_id] = result.output
            results.append(step_result)

        return results
