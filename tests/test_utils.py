import unittest
from unittest.mock import MagicMock, patch
import os
from utils import save_image_artifact
from PIL import Image as PILImage

class TestUtils(unittest.TestCase):
    def setUp(self):
        # Mock dependencies
        self.mock_image_class = patch('utils.Image').start()
        self.mock_db = patch('utils.db').start()

        # Setup mock image
        self.mock_pil_image = MagicMock(spec=PILImage.Image)
        self.mock_pil_image.width = 100
        self.mock_pil_image.height = 50
        self.mock_pil_image.mode = 'RGB'

        self.user_id = 1
        self.upload_folder = '/tmp/test_uploads'

    def tearDown(self):
        patch.stopall()

    def test_save_image_artifact_sync(self):
        # Test synchronous saving
        self.mock_pil_image.save = MagicMock()

        save_image_artifact(
            pil_image=self.mock_pil_image,
            user_id=self.user_id,
            upload_folder=self.upload_folder,
            filename_prefix="test_",
            metadata={'display_name': 'My Pic'},
            executor=None
        )

        # Check if file save was called
        self.mock_pil_image.save.assert_called_once()
        args, _ = self.mock_pil_image.save.call_args
        self.assertTrue(args[0].startswith(os.path.join(self.upload_folder, 'test_')))
        self.assertTrue(args[0].endswith('.bmp'))
        self.assertEqual(args[1], 'BMP')

        # Check DB calls
        self.mock_image_class.assert_called_once()
        call_kwargs = self.mock_image_class.call_args[1]
        self.assertEqual(call_kwargs['user_id'], self.user_id)
        self.assertEqual(call_kwargs['display_name'], 'My Pic')

        self.mock_db.session.add.assert_called_once()
        self.mock_db.session.commit.assert_called_once()

    def test_save_image_artifact_async(self):
        # Test async saving
        mock_executor = MagicMock()
        mock_future = MagicMock()
        mock_executor.submit.return_value = mock_future

        save_image_artifact(
            pil_image=self.mock_pil_image,
            user_id=self.user_id,
            upload_folder=self.upload_folder,
            executor=mock_executor
        )

        mock_executor.submit.assert_called_once()
        mock_future.result.assert_called_once()
        self.mock_db.session.commit.assert_called_once()

    def test_save_image_artifact_async_failure(self):
        # Test async saving failure (DB rollback)
        mock_executor = MagicMock()
        mock_future = MagicMock()
        mock_executor.submit.return_value = mock_future
        mock_future.result.side_effect = Exception("Save failed")

        # Mock DB image instance so we can check delete
        mock_db_instance = MagicMock()
        self.mock_image_class.return_value = mock_db_instance

        with self.assertRaises(Exception):
            save_image_artifact(
                pil_image=self.mock_pil_image,
                user_id=self.user_id,
                upload_folder=self.upload_folder,
                executor=mock_executor
            )

        self.mock_db.session.add.assert_called_once()
        # logic: commit() after add. exception. delete(). commit().
        self.assertEqual(self.mock_db.session.commit.call_count, 2)

        self.mock_db.session.delete.assert_called_with(mock_db_instance)

    def test_convert_to_rgb(self):
        self.mock_pil_image.mode = 'RGBA'
        converted_mock = MagicMock()
        converted_mock.width = 100
        converted_mock.height = 50
        self.mock_pil_image.convert.return_value = converted_mock

        save_image_artifact(
            pil_image=self.mock_pil_image,
            user_id=self.user_id,
            upload_folder=self.upload_folder
        )

        self.mock_pil_image.convert.assert_called_with('RGB')
        converted_mock.save.assert_called_once()

if __name__ == '__main__':
    unittest.main()
