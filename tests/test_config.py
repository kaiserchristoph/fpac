import unittest
import os
from unittest.mock import patch
from app import create_app

class ConfigTestCase(unittest.TestCase):
    def test_secret_key_default(self):
        """Test that the app uses the default secret key if not provided in environment."""
        with patch.dict(os.environ, {}, clear=True):
            app = create_app()
            self.assertEqual(app.config['SECRET_KEY'], 'dev-secret-key')

    def test_secret_key_override(self):
        """Test that the app uses the SECRET_KEY from environment if provided."""
        test_key = 'production-secret-key-123'
        with patch.dict(os.environ, {'SECRET_KEY': test_key}):
            app = create_app()
            self.assertEqual(app.config['SECRET_KEY'], test_key)

if __name__ == '__main__':
    unittest.main()
