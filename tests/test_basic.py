import unittest
from app import create_app
from extensions import db

class BasicTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'
        })
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

    def test_index(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_login_page(self):
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)

    def test_register_page(self):
        response = self.client.get('/register')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
