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
        # Target W=32 -> H=32. (32, 32). Valid (32<=32).
        # Target H=16 -> W=16. (16, 16). Valid (16<=64).
        # Both valid. 32/100 = 0.32 vs 16/100 = 0.16.
        # Pick largest scale: 32x32.

        self.assertEqual(image_record.width, 32)
        self.assertEqual(image_record.height, 32)

        # Verify file exists
        filepath = os.path.join(self.upload_folder, image_record.filename)
        self.assertTrue(os.path.exists(filepath))
        with Image.open(filepath) as saved_img:
            self.assertEqual(saved_img.size, (32, 32))

    def test_upload_resize_scrolling(self):
        # Create a wide image
        # 100x20. Target Height = 16. Scale = 16/20 = 0.8.
        # New Width = 100 * 0.8 = 80.
        # Max Width = 64.
        # 80 > 64. Must Scale to Width=64.
        # Scale Limit = 64/80 = 0.8.
        # New Height = 16 * 0.8 = 12.8 -> 12.
        # Result: 64x12.
        img = Image.new('RGB', (100, 20), color='blue')
        img_io = io.BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)

        # Upload with display_index=0, scroll_direction='left', scroll_speed=10
        response = self.client.post('/upload', data={
            'file': (img_io, 'wide.png'),
            'display_index': '0',
            'scroll_direction': 'left',
            'scroll_speed': '10'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)

        # Check DB
        # Order by id desc to get latest
        image_record = ImageModel.query.order_by(ImageModel.id.desc()).first()
        self.assertEqual(image_record.scroll_direction, 'left')
        self.assertEqual(image_record.scroll_speed, 10)

        self.assertEqual(image_record.width, 64)
        self.assertEqual(image_record.height, 12)

    def test_upload_scroll_speed_zero(self):
        # Create a wide image
        # 100x20.
        # Target W=32 -> H=32*(20/100)=6.4->6. Fits max_height(32).
        # Target H=16 -> W=16*(100/20)=80. Exceeds max_width(64).
        # Should result in 32x6.
        img = Image.new('RGB', (100, 20), color='green')
        img_io = io.BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)

        # Upload with display_index=0, scroll_direction='left', scroll_speed=0
        # Should fallback to no scroll logic (fit in display)
        response = self.client.post('/upload', data={
            'file': (img_io, 'speed0.png'),
            'display_index': '0',
            'scroll_direction': 'left',
            'scroll_speed': '0'
        }, follow_redirects=True)

        image_record = ImageModel.query.order_by(ImageModel.id.desc()).first()
        # Logic says if speed=0, direction forced to 'none'
        self.assertEqual(image_record.scroll_direction, 'none')
        self.assertEqual(image_record.scroll_speed, 0)

        self.assertEqual(image_record.width, 32)
        self.assertEqual(image_record.height, 6)

if __name__ == '__main__':
    unittest.main()
