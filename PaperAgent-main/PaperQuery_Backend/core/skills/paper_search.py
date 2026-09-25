"""paper_search：包装 arxiv_client，返回结构化论文列表。"""
from __future__ import annotations

from pydantic import BaseModel, Field

from core.skills.base import BaseSkill, SkillResult


class PaperSearchInput(BaseModel):
    keywords: list[str] = Field(default_factory=list)
    max_results: int = 10


class PaperSearchSkill(BaseSkill):
    name = "paper_search"
    description = "按关键词搜索 arXiv，返回结构化论文元数据列表"
    input_model = PaperSearchInput

    async def execute(self, data: PaperSearchInput, ctx: dict) -> SkillResult:
        if not data.keywords:
            return SkillResult(ok=False, error_code="BAD_INPUT", error_message="关键词为空")
        from arxiv_client import PARAMS, ArxivClient

        client = ArxivClient(max_results=data.max_results)
        fetch_params = [
            PARAMS.TITLE,
            PARAMS.AUTHORS,
            PARAMS.ABSTRACT,
            PARAMS.PUBLISHED,
            PARAMS.PDF_URL,
        ]
        try:
            papers = client.fetch_results(data.keywords, fetch_params)
        except Exception as e:
            return SkillResult(ok=False, error_code="SEARCH_ERROR", error_message=str(e))
        artifact = {
            "type": "paper_list",
            "title": ", ".join(data.keywords),
            "papers": papers,
        }
        return SkillResult(ok=True, output={"papers": papers}, artifacts=[artifact])
