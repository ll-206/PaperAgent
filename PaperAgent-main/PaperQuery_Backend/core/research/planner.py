"""Research Planner：把科研目标拆解为有限技能集合中的计划。"""
from __future__ import annotations

import json
import re

from core.research.schemas import TaskPlan
from core.skills.registry import SkillRegistry

PLANNER_PROMPT = """你是科研任务规划器。根据用户的科研目标，把任务拆解为可执行的步骤序列。

可用技能（skill 只能是以下之一，不得凭空生成）：
{skills}

严格输出 JSON，格式：
{{"goal": "...", "steps": [{{"step_id": "s1", "title": "...", "skill": "<可用技能名>", "depends_on": [], "input": {{}}, "success_criteria": ["..."]}}], "expected_artifacts": ["comparison_table", "report"]}}

用户目标：{goal}
"""


def _clean_json(text: str) -> str:
    text = re.sub(r"\s*```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```\s*", "", text)
    return text.strip()


class Planner:
    def __init__(self, llm, registry: SkillRegistry):
        self.llm = llm
        self.registry = registry

    def plan(self, goal: str, task_id: str | None = None) -> TaskPlan:
        skills_desc = json.dumps(self.registry.describe(), ensure_ascii=False)
        prompt = PLANNER_PROMPT.format(skills=skills_desc, goal=goal)
        resp = self.llm.invoke(prompt)
        text = resp.content if hasattr(resp, "content") else str(resp)
        data = json.loads(_clean_json(text))
        if not task_id:
            import uuid
            task_id = uuid.uuid4().hex[:12]
        data["task_id"] = task_id
        plan = TaskPlan.model_validate(data)
        self._validate_plan(plan)
        return plan

    def _validate_plan(self, plan: TaskPlan) -> None:
        """静态校验：skill 必须已注册；依赖不能引用不存在的 step。"""
        valid_skills = set(self.registry.names())
        step_ids = {s.step_id for s in plan.steps}
        for s in plan.steps:
            if s.skill not in valid_skills:
                raise ValueError(f"未知技能 {s.skill}（step {s.step_id}）")
            for dep in s.depends_on:
                if dep not in step_ids:
                    raise ValueError(f"step {s.step_id} 依赖不存在的 step {dep}")
