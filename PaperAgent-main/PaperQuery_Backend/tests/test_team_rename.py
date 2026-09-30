import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core.backend.db.database import Base
from core.backend.db.models import Team, TeamMember, TeamRequest, User
from core.backend.router.dependencies import get_db
from core.backend.router.router_team import router as team_router
from core.backend.router.router_user import router as user_router
from core.backend.utils.utils import get_current_user


class TeamRenameTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        with self.Session() as db:
            db.add_all([
                User(username="admin", password="unused", lid="team-1", role="admin"),
                User(username="other", password="unused", lid="team-2", role="admin"),
                User(username="member", password="unused", lid="member-lid", role="user"),
                Team(team_id="team-1", owner_username="admin", team_name="旧团队"),
                Team(team_id="team-2", owner_username="other", team_name="另一个团队"),
                TeamMember(team_id="team-1", member_username="member", member_lid="member-lid"),
            ])
            db.commit()

        def test_db():
            with self.Session() as db:
                yield db

        self.actor = "admin"

        def test_user():
            with self.Session() as db:
                return db.query(User).filter(User.username == self.actor).one()

        app = FastAPI()
        app.include_router(team_router)
        app.include_router(user_router)
        app.dependency_overrides[get_db] = test_db
        app.dependency_overrides[get_current_user] = test_user
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        self.engine.dispose()

    def test_admin_rename_persists_and_new_name_accepts_join_request(self):
        response = self.client.post("/team/rename", json={"team_name": "  新团队  "})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"], {"team_id": "team-1", "team_name": "新团队"})
        self.assertEqual(self.client.get("/team/info").json()["data"]["team_name"], "新团队")
        with self.Session() as db:
            self.assertEqual(db.query(TeamMember).filter_by(member_username="member").one().team_id, "team-1")

        registration = self.client.post("/register", json={
            "username": "new_member", "password": "secure-pass-123", "team_name": "新团队",
        })
        self.assertEqual(registration.status_code, 201)
        with self.Session() as db:
            self.assertEqual(db.query(TeamRequest).filter_by(applicant_username="new_member").one().team_id, "team-1")

    def test_non_admin_cannot_rename_and_invalid_or_duplicate_names_fail(self):
        self.actor = "member"
        self.assertEqual(self.client.post("/team/rename", json={"team_name": "成员命名"}).status_code, 403)
        self.actor = "admin"
        for name in ["  ", "x" * 51]:
            self.assertEqual(self.client.post("/team/rename", json={"team_name": name}).status_code, 422)
        for name in ["另一个团队", "other"]:
            self.assertEqual(self.client.post("/team/rename", json={"team_name": name}).status_code, 409)
        with self.Session() as db:
            self.assertEqual(db.query(Team).filter_by(team_id="team-1").one().team_name, "旧团队")


if __name__ == "__main__":
    unittest.main()
