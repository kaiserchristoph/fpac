import unittest
from app import create_app
from extensions import db
from models import User

class UserModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'
        })
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_hashing(self):
        u = User(username='susan')
        u.set_password('cat')
        self.assertFalse(u.check_password('dog'))
        self.assertTrue(u.check_password('cat'))

    def test_password_salts_are_random(self):
        u = User(username='susan')
        u.set_password('cat')
        u2 = User(username='david')
        u2.set_password('cat')
        self.assertTrue(u.password_hash != u2.password_hash)

if __name__ == '__main__':
    unittest.main()
