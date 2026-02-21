import unittest
import tempfile
import shutil
import os
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

    def test_rgb_endpoint(self):
        # Create a dummy image
        img = PILImage.new('RGB', (2, 2), color='red')
        filename = 'test_image.bmp'
        filepath = os.path.join(self.test_dir, filename)
        img.save(filepath)

        with self.app.app_context():
            # Get user id
            user = User.query.filter_by(username='test').first()
            db_img = Image(filename=filename, user_id=user.id, width=2, height=2)
            db.session.add(db_img)
            db.session.commit()
            img_id = db_img.id

        response = self.client.get(f'/api/image/{img_id}/rgb')

        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertEqual(json_data['width'], 2)
        self.assertEqual(json_data['height'], 2)
        # Verify pixels: red is [255, 0, 0]
        # Should be [[255,0,0], [255,0,0], [255,0,0], [255,0,0]]
        self.assertEqual(json_data['pixels'], [[255, 0, 0], [255, 0, 0], [255, 0, 0], [255, 0, 0]])
