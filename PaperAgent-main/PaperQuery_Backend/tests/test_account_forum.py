import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core.backend.db.database import Base
from core.backend.db.models import User
from core.backend.router.dependencies import get_db
from main import app


class AccountForumTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

        def test_db():
            with self.Session() as db:
                yield db

        app.dependency_overrides[get_db] = test_db
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()
        self.client.close()
        self.engine.dispose()

    def test_registration_hash_login_and_forum_category(self):
        credentials = {'username': 'new_researcher', 'password': 'strong_password_123'}
        self.assertEqual(self.client.post('/register', json=credentials).status_code, 201)
        self.assertEqual(self.client.post('/register', json=credentials).status_code, 409)
        with self.Session() as db:
            self.assertTrue(db.query(User).filter(User.username == credentials['username']).one().password.startswith('pbkdf2_sha256$'))
        login = self.client.post('/login', json=credentials)
        self.assertEqual(login.status_code, 200)
        headers = {'Authorization': f"Bearer {login.json()['data']['access_token']}"}
        created = self.client.post('/forum/createpost', headers=headers, json={
            'title': '研究笔记', 'content': '测试分类', 'category': '学习',
        })
        self.assertEqual(created.status_code, 200)
        posts = self.client.get('/forum/getallpost', headers=headers).json()['data']
        self.assertEqual(posts[0]['category'], '学习')
        invalid = self.client.post('/forum/createpost', headers=headers, json={
            'title': '错误分类', 'content': '', 'category': 'invalid',
        })
        self.assertEqual(invalid.status_code, 422)


if __name__ == '__main__':
    unittest.main()
