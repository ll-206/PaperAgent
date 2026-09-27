import os
import unittest
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


if __name__ == "__main__":
    unittest.main()
