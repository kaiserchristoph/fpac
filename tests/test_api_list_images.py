import unittest
import tempfile
import shutil
import os
import json
from app import create_app, db
from models import User, Image

class APIListImagesTestCase(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.app = create_app({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'UPLOAD_FOLDER': self.test_dir,
            'WTF_CSRF_ENABLED': False  # Disable CSRF for testing
        })
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            # Create a user
            u = User(username='testuser')
            u.set_password('password')
            db.session.add(u)
            db.session.commit()
            self.user_id = u.id

    def tearDown(self):
        shutil.rmtree(self.test_dir)
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_list_images_empty(self):
        response = self.client.get('/api/images')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('images', data)
        self.assertEqual(data['images'], [])

    def test_list_images_populated(self):
        with self.app.app_context():
            img1 = Image(
                filename='test1.bmp',
                user_id=self.user_id,
                width=32,
                height=16,
                display_name='Test Image 1',
                scroll_direction='left',
                scroll_speed=5
            )
            img2 = Image(
                filename='test2.bmp',
                user_id=self.user_id,
                width=64,
                height=32,
                display_name='Test Image 2',
                scroll_direction='right',
                scroll_speed=10
            )
            db.session.add_all([img1, img2])
            db.session.commit()

        response = self.client.get('/api/images')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('images', data)
        self.assertEqual(len(data['images']), 2)

        # Verify the first image (order isn't guaranteed by API unless sorted, but here we can find by filename)
        img_data_1 = next((img for img in data['images'] if img['filename'] == 'test1.bmp'), None)
        self.assertIsNotNone(img_data_1)
        self.assertEqual(img_data_1['width'], 32)
        self.assertEqual(img_data_1['height'], 16)
        self.assertEqual(img_data_1['display_name'], 'Test Image 1')
        self.assertEqual(img_data_1['scroll_direction'], 'left')
        self.assertEqual(img_data_1['scroll_speed'], 5)
        # Verify URL structure
        self.assertIn('uploads/test1.bmp', img_data_1['url'])

        # Verify the second image
        img_data_2 = next((img for img in data['images'] if img['filename'] == 'test2.bmp'), None)
        self.assertIsNotNone(img_data_2)
        self.assertEqual(img_data_2['width'], 64)
        self.assertEqual(img_data_2['height'], 32)
        self.assertEqual(img_data_2['display_name'], 'Test Image 2')
        self.assertEqual(img_data_2['scroll_direction'], 'right')
        self.assertEqual(img_data_2['scroll_speed'], 10)
        self.assertIn('uploads/test2.bmp', img_data_2['url'])

if __name__ == '__main__':
    unittest.main()
