import unittest
from unittest.mock import MagicMock, patch
from PIL import Image
import utils

class TestResizeLogic(unittest.TestCase):

    def setUp(self):
        self.display_config = {
            'width': 32,
            'height': 16,
            'max_width': 64,
            'max_height': 32
        }

    def test_smaller_image(self):
        # Image is 10x10, fits within 32x16. Should not be resized.
        image = Image.new('RGB', (10, 10))
        resized_image = utils.resize_image_to_display(image, self.display_config)
        self.assertEqual(resized_image.size, (10, 10))
        self.assertIs(resized_image, image)  # Should return same object if no resize

    def test_wider_image(self):
        # Image is 100x10.
        # Target Width = 32. Scale = 0.32. New Height = 3.2 -> 3.
        # 3 <= Max Height (32). Valid.
        # Target Height = 16. Scale = 1.6. New Width = 160.
        # 160 <= Max Width (64). Invalid.
        # Expected: Resize to Width=32.
        image = Image.new('RGB', (100, 10))

        with patch.object(Image.Image, 'resize', return_value=MagicMock(size=(32, 3))) as mock_resize:
            resized_image = utils.resize_image_to_display(image, self.display_config)

            # Check arguments
            args, kwargs = mock_resize.call_args
            self.assertEqual(args[0], (32, 3))
            self.assertEqual(kwargs.get('resample'), Image.NEAREST)

    def test_taller_image(self):
        # Image is 10x100.
        # Target Width = 32. Scale = 3.2. New Height = 320.
        # 320 <= Max Height (32). Invalid.
        # Target Height = 16. Scale = 0.16. New Width = 1.6 -> 1 or 2 depending on rounding. Let's say 2.
        # 2 <= Max Width (64). Valid.
        # Expected: Resize to Height=16.
        image = Image.new('RGB', (10, 100))

        expected_width = int(10 * (16 / 100)) # 1

        with patch.object(Image.Image, 'resize', return_value=MagicMock(size=(expected_width, 16))) as mock_resize:
            resized_image = utils.resize_image_to_display(image, self.display_config)

            args, kwargs = mock_resize.call_args
            self.assertEqual(args[0][1], 16) # Height should match display height
            self.assertEqual(kwargs.get('resample'), Image.NEAREST)

    def test_large_image_fits_both(self):
        # Image is 64x32. Matches max dimensions exactly.
        image = Image.new('RGB', (64, 32))

        with patch.object(Image.Image, 'resize', return_value=MagicMock(size=(32, 16))) as mock_resize:
            resized_image = utils.resize_image_to_display(image, self.display_config)

            args, kwargs = mock_resize.call_args
            self.assertEqual(args[0], (32, 16))

    def test_large_image_ambiguous(self):
        # Image is 40x40.
        # Target Width = 32. Scale = 0.8. New Height = 32. Fits Max Height (32). Valid.
        # Target Height = 16. Scale = 0.4. New Width = 16. Fits Max Width (64). Valid.
        # Both valid. 0.8 > 0.4. Should pick scale 0.8 -> 32x32.
        image = Image.new('RGB', (40, 40))

        with patch.object(Image.Image, 'resize', return_value=MagicMock(size=(32, 32))) as mock_resize:
            resized_image = utils.resize_image_to_display(image, self.display_config)

            args, kwargs = mock_resize.call_args
            self.assertEqual(args[0], (32, 32))

    def test_horizontal_scroll_fit_height(self):
        # Image is 100x100.
        # Horizontal scroll (left/right). Should fit height (16).
        image = Image.new('RGB', (100, 100))

        with patch.object(Image.Image, 'resize', return_value=MagicMock(size=(16, 16))) as mock_resize:
            resized_image = utils.resize_image_to_display(image, self.display_config, scroll_direction='left')

            # Check arguments
            if mock_resize.called:
                args, kwargs = mock_resize.call_args
                self.assertEqual(args[0][1], 16) # Height should be 16
                self.assertEqual(kwargs.get('resample'), Image.NEAREST)
            else:
                 self.fail("Resize not called for horizontal scroll")

    def test_horizontal_scroll_cap_width(self):
        # Image is 1000x100.
        # Target Height = 16. Scale = 0.16. New Width = 160.
        # 160 > Max Width (64). Must scale down to Width=64.
        image = Image.new('RGB', (1000, 100))

        with patch.object(Image.Image, 'resize', return_value=MagicMock(size=(64, 6))) as mock_resize:
            resized_image = utils.resize_image_to_display(image, self.display_config, scroll_direction='right')

            args, kwargs = mock_resize.call_args
            self.assertEqual(args[0][0], 64) # Width should be max width

    def test_vertical_scroll_fit_width(self):
        # Image is 100x100.
        # Vertical scroll (up/down). Should fit width (32).
        image = Image.new('RGB', (100, 100))

        with patch.object(Image.Image, 'resize', return_value=MagicMock(size=(32, 32))) as mock_resize:
            resized_image = utils.resize_image_to_display(image, self.display_config, scroll_direction='up')

            args, kwargs = mock_resize.call_args
            self.assertEqual(args[0][0], 32) # Width should be 32

    def test_vertical_scroll_cap_height(self):
        # Image is 100x1000.
        # Target Width = 32. Scale = 0.32. New Height = 320.
        # 320 > Max Height (32). Must scale to Height=32.
        image = Image.new('RGB', (100, 1000))

        with patch.object(Image.Image, 'resize', return_value=MagicMock(size=(3, 32))) as mock_resize:
            resized_image = utils.resize_image_to_display(image, self.display_config, scroll_direction='down')

            args, kwargs = mock_resize.call_args
            self.assertEqual(args[0][1], 32) # Height should be max height

if __name__ == '__main__':
    unittest.main()
