import unittest
import io
import os
import tempfile
import shutil
from app import create_app
from extensions import db
from models import User

class UploadLimitTestCase(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for uploads
        self.upload_folder = tempfile.mkdtemp()

        # Configure app for testing
        test_config = {
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'UPLOAD_FOLDER': self.upload_folder,
            'WTF_CSRF_ENABLED': False # Disable CSRF for testing
        }
        self.app = create_app(test_config)

        self.client = self.app.test_client()

        # Create db and user
        with self.app.app_context():
            db.create_all()
            user = User(username='testuser')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()

        # Login
        self.client.post('/login', data={'username': 'testuser', 'password': 'password'})

    def tearDown(self):
        # Clean up temp folder
        if os.path.exists(self.upload_folder):
            shutil.rmtree(self.upload_folder)

    def test_upload_large_file(self):
        # Create a large dummy file (3MB)
        # 3 * 1024 * 1024 = 3,145,728 bytes
        large_data = b'a' * (3 * 1024 * 1024)
        data = {
            'file': (io.BytesIO(large_data), 'large.bmp')
        }

        # Attempt to upload
        # We expect 413 Request Entity Too Large if the fix is applied.
        # If not applied, it will likely be 302 (redirect) or 200.
        response = self.client.post('/upload', data=data, content_type='multipart/form-data')

        self.assertEqual(response.status_code, 413, f"Expected 413, got {response.status_code}")

if __name__ == '__main__':
    unittest.main()
