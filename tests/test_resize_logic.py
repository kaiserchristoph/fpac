import unittest
from PIL import Image
from utils import resize_image_to_display

class TestResizeLogic(unittest.TestCase):
    def setUp(self):
        self.display_config = {
            'width': 32,
            'height': 16,
            'max_width': 320,
            'max_height': 320,
            'name': 'TestDisplay'
        }

    def test_no_scroll_fit_width(self):
        # Image larger than display, fits by width
        img = Image.new('RGB', (64, 32)) # 2x larger
        resized = resize_image_to_display(img, self.display_config, 'none', 0)
        self.assertEqual(resized.size, (32, 16))

    def test_no_scroll_fit_height(self):
        # Image larger than display, fits by height
        img = Image.new('RGB', (32, 64)) # Tall image
        # Fit 32x64 into 32x16.
        # Height is limiting factor. 16/64 = 0.25. Width 32*0.25 = 8.
        # So 8x16.
        resized = resize_image_to_display(img, self.display_config, 'none', 0)
        self.assertEqual(resized.size, (8, 16))

    def test_no_scroll_smaller(self):
        # Image smaller than display
        img = Image.new('RGB', (10, 10))
        resized = resize_image_to_display(img, self.display_config, 'none', 0)
        self.assertEqual(resized.size, (10, 10))

    def test_horizontal_scroll_resize_height(self):
        # Tall image, horizontal scroll. Should resize height to 16.
        img = Image.new('RGB', (100, 100))
        # Height 100 -> 16. Width 100 -> 16.
        resized = resize_image_to_display(img, self.display_config, 'left', 10)
        self.assertEqual(resized.size, (16, 16))

    def test_horizontal_scroll_no_resize(self):
        # Short image, horizontal scroll. Height < 16. Should not resize.
        img = Image.new('RGB', (100, 10))
        resized = resize_image_to_display(img, self.display_config, 'left', 10)
        self.assertEqual(resized.size, (100, 10))

    def test_vertical_scroll_resize_width(self):
        # Wide image, vertical scroll. Should resize width to 32.
        img = Image.new('RGB', (100, 100))
        # Width 100 -> 32. Height 100 -> 32.
        resized = resize_image_to_display(img, self.display_config, 'up', 10)
        self.assertEqual(resized.size, (32, 32))

    def test_vertical_scroll_no_resize(self):
        # Narrow image, vertical scroll. Width < 32. Should not resize.
        img = Image.new('RGB', (10, 100))
        resized = resize_image_to_display(img, self.display_config, 'up', 10)
        self.assertEqual(resized.size, (10, 100))

    def test_scroll_speed_zero_behavior(self):
        # Scroll options set but speed 0. Should behave like no scroll (fit to display).
        img = Image.new('RGB', (100, 100))
        # Should fit into 32x16.
        # Height constrained -> 16. Width -> 16. (Since aspect ratio 1:1)
        # Wait, if aspect 1:1, fitting in 32x16 means height=16, width=16.
        resized = resize_image_to_display(img, self.display_config, 'left', 0)
        self.assertEqual(resized.size, (16, 16))

    def test_scroll_direction_none_behavior(self):
        # Speed > 0 but direction none. Should behave like no scroll.
        img = Image.new('RGB', (100, 100))
        resized = resize_image_to_display(img, self.display_config, 'none', 10)
        self.assertEqual(resized.size, (16, 16))

if __name__ == '__main__':
    unittest.main()
