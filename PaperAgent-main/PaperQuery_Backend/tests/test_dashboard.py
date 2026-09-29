import os
import unittest
from datetime import datetime, timedelta, timezone

import jwt
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core.backend.db.database import Base
from core.backend.db.models import ActivityEvent, Document, Knowledge, Note, User
from core.backend.router.dependencies import get_db
from main import app


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        with self.Session() as db:
            db.add_all([
                User(username="alice", password="x", lid="alice-lid"),
                User(username="bob", password="x", lid="bob-lid"),
                Knowledge(knowledgeID="a", lid="alice-lid", knowledgeName="Alice Library", documentNum=1, vectorNum=3),
                Knowledge(knowledgeID="b", lid="bob-lid", knowledgeName="Bob Library", documentNum=1, vectorNum=2),
                Document(uid="a-doc", knowledgeID="a", lid="alice-lid", documentName="a.pdf", documentPath="a.pdf", createTime=datetime.now()),
                Document(uid="b-doc", knowledgeID="b", lid="bob-lid", documentName="b.pdf", documentPath="b.pdf", createTime=datetime.now()),
                Note(knowledgeID="a", lid="alice-lid", uid="a-doc", note="# Alice note"),
                Note(knowledgeID="b", lid="bob-lid", uid="b-doc", note="# Bob note"),
                ActivityEvent(lid="alice-lid", event_type="ask"),
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

    def headers(self, username="alice"):
        token = jwt.encode({"username": username, "exp": datetime.now(timezone.utc) + timedelta(minutes=10)},
                           os.environ["SECRET_KEY"], algorithm=os.environ["ALGORITHM"])
        return {"Authorization": f"Bearer {token}"}

    def test_account_scoped_overview_notes_and_reading(self):
        overview = self.client.get("/dashboard/overview", headers=self.headers()).json()["data"]
        self.assertEqual(overview["stats"]["askCount"], 1)
        self.assertEqual(overview["stats"]["libraries"], 1)
        notes = self.client.get("/notes/collection", headers=self.headers()).json()["data"]
        self.assertEqual([item["documentName"] for item in notes], ["a.pdf"])

        denied = self.client.post("/dashboard/reading", headers=self.headers(), json={"knowledgeID": "b", "documentID": "b-doc", "seconds": 30})
        self.assertEqual(denied.status_code, 404)
        allowed = self.client.post("/dashboard/reading", headers=self.headers(), json={"knowledgeID": "a", "documentID": "a-doc", "seconds": 30})
        self.assertEqual(allowed.status_code, 200)
        updated = self.client.get("/dashboard/overview", headers=self.headers()).json()["data"]
        self.assertEqual(updated["readings"][0]["seconds"], 30)
        self.assertTrue(updated["readings"][0]["hasNote"])
        self.assertEqual(self.client.get("/dashboard/overview").status_code, 401)


if __name__ == "__main__":
    unittest.main()
