import os
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from datetime import datetime, timedelta, timezone

import jwt
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core.backend.db.database import Base
from core.backend.db.models import Document, TMPDocument, User
from core.backend.router.dependencies import get_db
from main import app
from core.skills.base import SkillResult
from core.common.types import EvidenceChunk
from core.decision.schemas import GroundingDecision


class AskAuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        with self.Session() as db:
            db.add_all([
                User(username="alice", password="unused", lid="alice-lid"),
                User(username="bob", password="unused", lid="bob-lid"),
                Document(uid="alice-paper", knowledgeID="a", lid="alice-lid", documentName="a.pdf", documentPath="a.pdf"),
                Document(uid="bob-paper", knowledgeID="b", lid="bob-lid", documentName="b.pdf", documentPath="b.pdf"),
                TMPDocument(uid="alice-temp", knowledgeID="tmp", lid="alice-lid", documentName="tmp.pdf", documentPath="tmp.pdf"),
            ])
            db.commit()

        def test_db():
            with self.Session() as db:
                yield db

        app.dependency_overrides[get_db] = test_db
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()
        self.client.close()
        self.engine.dispose()

    def token(self, username, expired=False):
        when = datetime.now(timezone.utc) + timedelta(minutes=-1 if expired else 10)
        return jwt.encode(
            {"username": username, "exp": when},
            os.environ["SECRET_KEY"], algorithm=os.environ["ALGORITHM"],
        )

    def ask(self, token=None, documents=None):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        return self.client.post(
            "/qa/stream", headers=headers,
            json={"question": "Summarize the selected paper", "document_ids": documents or []},
        )

    def test_missing_invalid_and_expired_jwt_are_rejected(self):
        self.assertEqual(self.ask().status_code, 401)
        self.assertEqual(self.ask("invalid.jwt.token").status_code, 401)
        self.assertEqual(self.ask(self.token("alice", expired=True)).status_code, 401)

    def test_other_accounts_document_is_rejected(self):
        response = self.ask(self.token("alice"), ["bob-paper"])
        self.assertEqual(response.status_code, 403)
        self.assertNotIn("bob.pdf", response.text)

    def test_mixed_ownership_is_rejected(self):
        self.assertEqual(self.ask(self.token("alice"), ["alice-paper", "bob-paper"]).status_code, 403)

    def test_owned_library_and_temporary_documents_are_allowed(self):
        self.assertEqual(self.ask(self.token("alice"), ["alice-paper"]).status_code, 200)
        self.assertEqual(self.ask(self.token("alice"), ["alice-temp"]).status_code, 200)

    def test_broad_recent_paper_request_has_useful_fallback_when_sources_fail(self):
        class UnavailableSearch:
            async def run(self, _args):
                return SkillResult(ok=False, error_code="SEARCH_ERROR", error_message="source unavailable")

        with patch.object(app, "chat_agents", {}, create=True), \
             patch.object(app, "decision_engine", None, create=True), \
             patch("core.backend.router.router_qa.PaperSearchSkill", UnavailableSearch):
            response = self.client.post(
                "/qa/stream",
                headers={"Authorization": f"Bearer {self.token('alice')}"},
                json={"question": "最近最新的论文有没有推荐的", "document_ids": []},
            )
        self.assertEqual(response.status_code, 200)
        self.assertIn("machine learning", response.text)
        self.assertIn("你想关注哪个方向", response.text)
        self.assertNotIn("请调整研究领域或关键词后重试", response.text)

    def test_general_question_without_papers_gets_normal_answer(self):
        class FakeAgent:
            def get_llm(self):
                return object()

            def chat_simple(self, _prompt):
                yield SimpleNamespace(content="RAG 把检索到的资料用于生成回答。")

        with patch.object(app, "chat_agents", {"deepseek": FakeAgent()}, create=True):
            response = self.client.post(
                "/qa/stream",
                headers={"Authorization": f"Bearer {self.token('alice')}"},
                json={"question": "什么是 RAG？", "document_ids": []},
            )
        self.assertEqual(response.status_code, 200)
        self.assertIn('"route": "GENERAL_CHAT"', response.text)
        self.assertIn("RAG 把检索到的资料用于生成回答", response.text)

    def test_bound_paper_overview_uses_pdf_evidence_even_if_intent_would_be_general(self):
        prompts = []

        class FakeAgent:
            def get_llm(self):
                return object()

            def chat_simple(self, prompt):
                prompts.append(prompt)
                yield SimpleNamespace(content="这篇论文讨论联邦学习。[C1]")

        class FakeDecisionEngine:
            def __init__(self, _llm):
                pass

            def decide_intent(self, *_args):
                raise AssertionError("明确指向已选论文时不应进入普通聊天分类")

            def decide_evidence(self, *_args):
                raise AssertionError("概述应直接使用论文开头的证据")

            def verify_grounding(self, *_args):
                return GroundingDecision(passed=True, confidence=1.0)

        class FakeChroma:
            def get_opening_evidence(self, document_ids):
                self.document_ids = document_ids
                return [EvidenceChunk(
                    chunk_id="alice-paper:p1", document_id="alice-paper",
                    source="a.pdf", page_number=1,
                    text="This paper proposes a federated learning method.",
                )]

            def search_evidence(self, *_args, **_kwargs):
                return []

        chroma = FakeChroma()
        with patch.object(app, "chat_agents", {"deepseek": FakeAgent()}, create=True), \
             patch.object(app, "chroma_db", chroma, create=True), \
             patch("core.backend.router.router_qa.DecisionEngine", FakeDecisionEngine):
            response = self.client.post(
                "/qa/stream",
                headers={"Authorization": f"Bearer {self.token('alice')}"},
                json={"question": "讲一下这篇论文", "document_ids": ["alice-paper"]},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(chroma.document_ids, ["alice-paper"])
        self.assertIn('"route": "LOCAL_RAG"', response.text)
        self.assertIn("这篇论文讨论联邦学习", response.text)
        self.assertIn('"id": "C1"', response.text)
        self.assertIn("a.pdf", prompts[0])
        self.assertIn("This paper proposes a federated learning method.", prompts[0])

    def test_bound_paper_without_index_reports_processing_instead_of_losing_binding(self):
        class FakeChroma:
            def get_opening_evidence(self, _document_ids):
                return []

            def search_evidence(self, *_args, **_kwargs):
                return []

        with patch.object(app, "chat_agents", {}, create=True), \
             patch.object(app, "decision_engine", None, create=True), \
             patch.object(app, "chroma_db", FakeChroma(), create=True):
            response = self.client.post(
                "/qa/stream",
                headers={"Authorization": f"Bearer {self.token('alice')}"},
                json={"question": "讲一下这篇论文", "document_ids": ["alice-paper"]},
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("已选定 a.pdf", response.text)
        self.assertIn("尚未读取到可用于问答的论文文本", response.text)


if __name__ == "__main__":
    unittest.main()
