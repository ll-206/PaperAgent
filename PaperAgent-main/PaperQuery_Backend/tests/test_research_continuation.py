import os
import unittest
from datetime import datetime, timedelta, timezone

import jwt
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core.backend.db.database import Base
from core.backend.db.models import Artifact, ResearchTask, User
from core.backend.router.dependencies import get_db
from core.research.schemas import TaskPlan, TaskState
from main import app


class FakeOrchestrator:
    def __init__(self):
        self.last_goal = ''
        self.last_context = {}

    def run(self, goal, context=None):
        self.last_goal, self.last_context = goal, context or {}
        plan = TaskPlan(task_id='next-task', goal=goal, steps=[])
        return TaskState(task_id='next-task', goal=goal, status='SUCCESS', plan=plan)


class ResearchContinuationTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        with self.Session() as db:
            db.add_all([
                User(username='alice', password='x', lid='alice-lid'),
                User(username='bob', password='x', lid='bob-lid'),
                ResearchTask(task_id='prior', lid='alice-lid', goal='研究方法 A', status='SUCCESS'),
                ResearchTask(task_id='other', lid='bob-lid', goal='私人研究', status='SUCCESS'),
                Artifact(artifact_id='prior-art', task_id='prior', type='research_report', title='第一轮报告', data_json='{"title":"第一轮报告","report":"发现了方法 A 的局限"}'),
            ])
            db.commit()

        def test_db():
            with self.Session() as db:
                yield db

        app.dependency_overrides[get_db] = test_db
        self.previous = getattr(app, 'research_orchestrator', None)
        self.fake = FakeOrchestrator()
        app.research_orchestrator = self.fake
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()
        app.research_orchestrator = self.previous
        self.client.close()
        self.engine.dispose()

    def headers(self):
        token = jwt.encode({'username': 'alice', 'exp': datetime.now(timezone.utc) + timedelta(minutes=10)}, os.environ['SECRET_KEY'], algorithm=os.environ['ALGORITHM'])
        return {'Authorization': f'Bearer {token}'}

    def test_continuation_uses_owned_prior_artifact(self):
        response = self.client.post('/research/tasks', headers=self.headers(), json={'goal': '深入实验', 'parent_task_id': 'prior'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('发现了方法 A 的局限', self.fake.last_goal)
        self.assertEqual(self.fake.last_context['parent_task_id'], 'prior')
        details = self.client.get('/research/tasks/next-task', headers=self.headers()).json()['data']
        self.assertEqual(details['parent_task_id'], 'prior')

    def test_cannot_continue_another_users_task(self):
        response = self.client.post('/research/tasks', headers=self.headers(), json={'goal': '窥探', 'parent_task_id': 'other'})
        self.assertEqual(response.status_code, 404)


if __name__ == '__main__':
    unittest.main()
