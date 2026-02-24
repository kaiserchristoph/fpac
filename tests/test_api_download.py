import unittest
import tempfile
import shutil
import os
from app import create_app, db
from models import User, Image

class ApiDownloadTestCase(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.app = create_app({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'UPLOAD_FOLDER': self.test_dir,
            'WTF_CSRF_ENABLED': False
        })
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

    def test_download_image_redirect(self):
        filename = 'test_image.png'
        # Create a dummy file in the upload folder
        filepath = os.path.join(self.test_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(b'fake image content')

        with self.app.app_context():
            user = User.query.filter_by(username='test').first()
            img = Image(filename=filename, user_id=user.id)
            db.session.add(img)
            db.session.commit()
            img_id = img.id

        response = self.client.get(f'/api/download/{img_id}')

        # Check for redirect
        self.assertEqual(response.status_code, 302)
        # Verify the redirect location
        # The location should end with /static/uploads/test_image.png
        self.assertTrue(response.location.endswith(f'/static/uploads/{filename}'))

    def test_download_nonexistent_image(self):
        response = self.client.get('/api/download/999')
        self.assertEqual(response.status_code, 404)
