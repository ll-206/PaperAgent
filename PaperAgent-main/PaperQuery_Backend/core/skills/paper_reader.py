"""paper_reader：按 documentID / page 读取论文原文。"""
from __future__ import annotations

import os

from pydantic import BaseModel

from core.skills.base import BaseSkill, SkillResult


class PaperReaderInput(BaseModel):
    document_id: str
    page: int = 1
    document_path: str = ""


class PaperReaderSkill(BaseSkill):
    name = "paper_reader"
    description = "按 documentID 与页码读取论文原文"
    input_model = PaperReaderInput

    async def execute(self, data: PaperReaderInput, ctx: dict) -> SkillResult:
        path = data.document_path
        if not path:
            db = ctx.get("db")
            if db is None:
                return SkillResult(ok=False, error_code="NO_DB", error_message="数据库未注入")
            from core.backend.crud.crud_document import get_document_by_uid

            doc = get_document_by_uid(db, data.document_id)
            if doc is None:
                return SkillResult(ok=False, error_code="NOT_FOUND", error_message="文档不存在")
            path = os.getenv("AcadeAgent_DIR", ".") + doc.documentPath

        if not os.path.exists(path):
            return SkillResult(ok=False, error_code="FILE_NOT_FOUND", error_message=f"文件不存在: {path}")

        import fitz

        pdf = fitz.open(path)
        try:
            if data.page < 1 or data.page > len(pdf):
                return SkillResult(ok=False, error_code="BAD_PAGE", error_message=f"页码越界: {data.page}")
            text = pdf.load_page(data.page - 1).get_text("text")
        finally:
            pdf.close()

        return SkillResult(
            ok=True,
            output={"text": text, "page": data.page, "document_id": data.document_id},
        )
