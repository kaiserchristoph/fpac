import unittest
from unittest.mock import patch, MagicMock
from app import create_app, db
from PIL import UnidentifiedImageError
from sqlalchemy.exc import SQLAlchemyError
import base64

class SaveDrawingErrorTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'WTF_CSRF_ENABLED': False
        })
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            # Create a user to log in
            from models import User
            user = User(username='testuser')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()

        # Login
        self.client.post('/login', data={'username': 'testuser', 'password': 'password'})

    def test_save_drawing_pil_error(self):
        # Simulate PIL error
        with patch('app.PILImage.open', side_effect=UnidentifiedImageError("Invalid image")):
            # Send a valid base64 payload
            payload = {
                'image': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII=',
                'display_name': 'test'
            }
            response = self.client.post('/save_drawing', json=payload)
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertFalse(data['success'])
            # Now it returns "Invalid image format"
            self.assertIn('Invalid image format', data['error'])

    def test_save_drawing_db_error(self):
        # Simulate DB error
        with patch('app.db.session.commit', side_effect=SQLAlchemyError("DB Error")):
             payload = {
                'image': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII=',
                'display_name': 'test'
            }
             # Mock PILImage.open to work because it's called before commit
             # Actually real PILImage.open works fine with the payload

             # Need to patch app.executor.submit to avoid threading issues if needed?
             # No, if db.commit fails, it throws immediately.
             # Wait, db.commit is called BEFORE future.result() check but AFTER future submission.
             # But the exception is caught in the outer try block.

             response = self.client.post('/save_drawing', json=payload)
             self.assertEqual(response.status_code, 200)
             data = response.get_json()
             self.assertFalse(data['success'])
             self.assertIn('Database error', data['error'])

if __name__ == '__main__':
    unittest.main()
