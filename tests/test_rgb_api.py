import unittest
import tempfile
import shutil
import os
import io
import base64
from app import create_app, db
from models import User, Image
from PIL import Image as PILImage

class RGBAPITestCase(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['UPLOAD_FOLDER'] = self.test_dir
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            # Create a user
            u = User(username='test')
            u.set_password('password')
            db.session.add(u)
            db.session.commit()

    def tearDown(self):
        shutil.rmtree(self.test_dir)
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_rgb_endpoint_with_display_info(self):
        # Create a dummy image
        img = PILImage.new('RGB', (2, 2), color='red')
        filename = 'test_image.bmp'
        filepath = os.path.join(self.test_dir, filename)
        img.save(filepath)

        with self.app.app_context():
            # Get user id
            user = User.query.filter_by(username='test').first()
            db_img = Image(
                filename=filename,
                user_id=user.id,
                width=2,
                height=2,
                display_name='TestDisplay',
                scroll_direction='left',
                scroll_speed=5
            )
            db.session.add(db_img)
            db.session.commit()
            img_id = db_img.id

        response = self.client.get(f'/api/image/{img_id}/rgb')

        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertEqual(json_data['width'], 2)
        self.assertEqual(json_data['height'], 2)
        self.assertEqual(json_data['display_name'], 'TestDisplay')
        self.assertEqual(json_data['scroll_direction'], 'left')
        self.assertEqual(json_data['scroll_speed'], 5)
        # Verify pixels: red is [255, 0, 0]
        # Should be [[255,0,0], [255,0,0], [255,0,0], [255,0,0]]
        self.assertEqual(json_data['pixels'], [[255, 0, 0], [255, 0, 0], [255, 0, 0], [255, 0, 0]])

    def test_save_drawing_with_display_info(self):
        # Login
        self.client.post('/login', data={'username': 'test', 'password': 'password'})

        # Create a tiny red image
        img = PILImage.new('RGB', (2, 2), color='red')
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        base64_img = base64.b64encode(img_byte_arr).decode('utf-8')
        data_url = f"data:image/png;base64,{base64_img}"

        response = self.client.post('/save_drawing', json={
            'image': data_url,
            'display_name': 'Standard 64x16',
            'scroll_direction': 'right',
            'scroll_speed': 10
        })

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()['success'])

        with self.app.app_context():
            img = Image.query.order_by(Image.id.desc()).first()
            self.assertEqual(img.display_name, 'Standard 64x16')
            self.assertEqual(img.scroll_direction, 'right')
            self.assertEqual(img.scroll_speed, 10)
