import unittest
from flask_login import current_user
from app import create_app
from extensions import db
from models import User

class RegistrationTestCase(unittest.TestCase):
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

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_registration_auto_login(self):
        with self.client:
            # Register a new user
            response = self.client.post('/register', data={
                'username': 'newuser',
                'password': 'password123'
            }, follow_redirects=True)

            # Check if the user is now logged in
            self.assertTrue(current_user.is_authenticated)
            self.assertEqual(current_user.username, 'newuser')

            # Check if redirected to the index page (or whatever page follows login)
            self.assertEqual(response.status_code, 200)

            # Verify we are on the index page by checking for some content unique to it
            self.assertIn(b'Welcome to Pixel Art App', response.data)

if __name__ == '__main__':
    unittest.main()
