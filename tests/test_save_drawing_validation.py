import unittest
from app import create_app, db
import json

class SaveDrawingValidationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'WTF_CSRF_ENABLED': False,
            'UPLOAD_FOLDER': '/tmp'
        })
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            from models import User
            user = User(username='testuser')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()

        # Login
        self.client.post('/login', data={'username': 'testuser', 'password': 'password'})

    def test_save_drawing_missing_image(self):
        # Missing 'image' key
        payload = {
            'display_name': 'test'
        }
        response = self.client.post('/save_drawing', json=payload)
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'Missing image data')

    def test_save_drawing_no_json(self):
        response = self.client.post('/save_drawing', data="not json", content_type='text/plain')
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'Missing image data')

if __name__ == '__main__':
    unittest.main()
