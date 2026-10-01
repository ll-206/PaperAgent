"""Regression tests for invalid generated plans and scoped PDF reads."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import fitz
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core.backend.db.database import Base
from core.backend.db.models import Document
from core.research.planner import Planner
from core.skills.builtin import LocalRetrievalSkill, ReportGenerateSkill
from core.skills.paper_reader import PaperReaderSkill
from core.skills.registry import SkillRegistry


class FakeLLM:
    def __init__(self, plans):
        self.plans = iter(plans)
        self.prompts = []

    def invoke(self, prompt):
        self.prompts.append(prompt)
        return json.dumps(next(self.plans))


def step(step_id, skill, input_data, depends_on=None):
    return {"step_id": step_id, "title": step_id, "skill": skill,
            "input": input_data, "depends_on": depends_on or []}


def plan(*steps):
    return {"goal": "test", "steps": list(steps), "expected_artifacts": []}


class PlannerGuardrailTests(unittest.TestCase):
    def setUp(self):
        registry = SkillRegistry()
        for skill in (PaperReaderSkill(), LocalRetrievalSkill(), ReportGenerateSkill()):
            registry.register(skill)
        self.registry = registry

    def test_repairs_wrong_input_type(self):
        bad = plan(step("s1", "paper_reader", {"document_id": ["paper-1"]}))
        good = plan(step("s1", "paper_reader", {"document_id": "paper-1"}))
        llm = FakeLLM([bad, good])
        result = Planner(llm, self.registry).plan("read", allowed_document_ids=["paper-1"])
        self.assertEqual(result.steps[0].input["document_id"], "paper-1")
        self.assertEqual(len(llm.prompts), 2)
        self.assertIn("paper-1", llm.prompts[0])

    def test_rejects_wrong_document_id_and_forward_dependency(self):
        invalid = plan(step("s1", "paper_reader", {"document_id": "other"}))
        llm = FakeLLM([invalid, invalid])
        with self.assertRaisesRegex(ValueError, "不允许"):
            Planner(llm, self.registry).plan("read", allowed_document_ids=["paper-1"])

        invalid = plan(step("s1", "report_generate", {"topic": "x"}, ["s2"]),
                       step("s2", "paper_reader", {"document_id": "paper-1"}))
        with self.assertRaisesRegex(ValueError, "尚未执行"):
            Planner(FakeLLM([invalid, invalid]), self.registry).plan(
                "read", allowed_document_ids=["paper-1"])

    def test_rejects_unlisted_reference_and_duplicate_step(self):
        invalid = plan(step("s1", "paper_reader", {"document_id": "paper-1"}),
                       step("s2", "report_generate", {"topic": "x", "context": "{{s1.result}}"}))
        with self.assertRaisesRegex(ValueError, "无效依赖"):
            Planner(FakeLLM([invalid, invalid]), self.registry).plan(
                "read", allowed_document_ids=["paper-1"])
        duplicate = plan(step("s1", "paper_reader", {"document_id": "paper-1"}),
                         step("s1", "paper_reader", {"document_id": "paper-1"}))
        with self.assertRaisesRegex(ValueError, "重复"):
            Planner(FakeLLM([duplicate, duplicate]), self.registry).plan(
                "read", allowed_document_ids=["paper-1"])


class PaperReaderScopeTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        pdf_path = Path(self.directory.name) / "paper.pdf"
        pdf = fitz.open()
        pdf.new_page().insert_text((72, 72), "Scoped paper content")
        pdf.save(pdf_path)
        pdf.close()
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        self.addCleanup(self.engine.dispose)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        with self.Session() as db:
            db.add_all([
                Document(uid="paper-1", knowledgeID="k", lid="mine", documentName="A", documentPath="/paper.pdf"),
                Document(uid="paper-2", knowledgeID="k", lid="other", documentName="B", documentPath="/paper.pdf"),
            ])
            db.commit()
        self.env = patch.dict(os.environ, {"AcadeAgent_DIR": self.directory.name})
        self.env.start()
        self.addCleanup(self.env.stop)

    async def test_rejects_path_and_out_of_scope_id(self):
        skill = PaperReaderSkill()
        ctx = {"db_factory": self.Session, "allowed_document_ids": ["paper-1"], "workspace_lid": "mine"}
        forbidden = await skill.run({"document_id": "paper-2"}, ctx)
        self.assertEqual(forbidden.error_code, "FORBIDDEN_DOCUMENT")
        path_injection = await skill.run({"document_id": "paper-1", "document_path": "/paper.pdf"}, ctx)
        self.assertFalse(path_injection.ok)
        allowed = await skill.run({"document_id": "paper-1"}, ctx)
        self.assertTrue(allowed.ok)
        self.assertIn("Scoped paper content", allowed.output["text"])

    async def test_workspace_scope_is_checked_in_database(self):
        result = await PaperReaderSkill().run(
            {"document_id": "paper-2"},
            {"db_factory": self.Session, "allowed_document_ids": ["paper-2"], "workspace_lid": "mine"},
        )
        self.assertEqual(result.error_code, "NOT_FOUND")
