import unittest
import os
import io
import shutil
from PIL import Image
from app import create_app
from extensions import db
from models import User, Image as ImageModel

class TestUploadResize(unittest.TestCase):
    def setUp(self):
        self.upload_folder = '/tmp/test_uploads'
        if not os.path.exists(self.upload_folder):
            os.makedirs(self.upload_folder)

        self.app = create_app({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'UPLOAD_FOLDER': self.upload_folder,
            'WTF_CSRF_ENABLED': False, # Disable CSRF for testing
            'DISPLAYS': [
                {'name': 'Test Display', 'width': 32, 'height': 16, 'max_width': 64, 'max_height': 32}
            ]
        })
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create user
        user = User(username='testuser')
        user.set_password('password')
        db.session.add(user)
        db.session.commit()

        # Login
        self.client.post('/login', data={'username': 'testuser', 'password': 'password'})

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        # Clean up files
        if os.path.exists(self.upload_folder):
            shutil.rmtree(self.upload_folder)

    def test_upload_resize(self):
        # Create a large image
        img = Image.new('RGB', (100, 100), color='red')
        img_io = io.BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)

        # Upload with display_index=0
        response = self.client.post('/upload', data={
            'file': (img_io, 'test.png'),
            'display_index': '0'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'File uploaded successfully', response.data)

        # Check DB
        image_record = ImageModel.query.first()
        self.assertIsNotNone(image_record)
        self.assertEqual(image_record.display_name, 'Test Display')

        # Check dimensions
        # 100x100 -> Resize to fit 32x16 (max 64x32).
        # Logic: fit within 32x16 strictly.
        # Height constrained -> 16. Width -> 16. (16, 16).

        self.assertEqual(image_record.width, 16)
        self.assertEqual(image_record.height, 16)

        # Verify file exists
        filepath = os.path.join(self.upload_folder, image_record.filename)
        self.assertTrue(os.path.exists(filepath))
        with Image.open(filepath) as saved_img:
            self.assertEqual(saved_img.size, (16, 16))

if __name__ == '__main__':
    unittest.main()
