import unittest
from flask_login import current_user
from app import create_app
from extensions import db
from models import User

class AuthTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'WTF_CSRF_ENABLED': False
        })
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        user = User(username='testuser')
        user.set_password('testpassword')
        db.session.add(user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_login_page_loads(self):
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login', response.data)

    def test_login_success(self):
        with self.client:
            response = self.client.post('/login', data={
                'username': 'testuser',
                'password': 'testpassword'
            }, follow_redirects=True)
            self.assertTrue(current_user.is_authenticated)
            self.assertEqual(response.status_code, 200)

    def test_login_failure_invalid_username(self):
        response = self.client.post('/login', data={
            'username': 'wronguser',
            'password': 'testpassword'
        }, follow_redirects=True)
        self.assertIn(b'Invalid username or password', response.data)

    def test_login_failure_invalid_password(self):
        response = self.client.post('/login', data={
            'username': 'testuser',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        self.assertIn(b'Invalid username or password', response.data)

    def test_logout(self):
        with self.client:
            self.client.post('/login', data={
                'username': 'testuser',
                'password': 'testpassword'
            }, follow_redirects=True)

            response = self.client.get('/logout', follow_redirects=True)
            self.assertFalse(current_user.is_authenticated)
            self.assertEqual(response.status_code, 200)

    def test_access_protected_route(self):
        response = self.client.get('/draw', follow_redirects=True)
        self.assertIn(b'Login', response.data)

if __name__ == '__main__':
    unittest.main()
