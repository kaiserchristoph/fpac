import os
from datetime import datetime, timezone
from extensions import db
from models import Image
from PIL import Image as PILImage

def save_image_artifact(pil_image, user_id, upload_folder, filename_prefix="image_", metadata=None, executor=None):
    """
    Saves a PIL Image to disk and creates a corresponding database record.

    Args:
        pil_image: The PIL Image object to save.
        user_id: The ID of the user saving the image.
        upload_folder: The directory path where the image file should be saved.
        filename_prefix: Prefix for the generated filename (default: "image_").
        metadata: Dictionary containing optional metadata ('display_name', 'scroll_direction', 'scroll_speed').
        executor: Optional concurrent.futures.Executor for asynchronous file saving. If None, saving is synchronous.

    Returns:
        The created Image database model instance.

    Raises:
        Exception: Re-raises exceptions from file saving or database operations.
    """
    if metadata is None:
        metadata = {}

    # Ensure image is RGB
    if pil_image.mode != 'RGB':
        pil_image = pil_image.convert('RGB')

    timestamp = int(datetime.now(timezone.utc).timestamp())
    filename = f"{filename_prefix}{user_id}_{timestamp}.bmp"
    filepath = os.path.join(upload_folder, filename)

    width = pil_image.width
    height = pil_image.height

    future = None
    if executor:
        future = executor.submit(pil_image.save, filepath, 'BMP')
    else:
        pil_image.save(filepath, 'BMP')

    db_image = Image(
        filename=filename,
        user_id=user_id,
        width=width,
        height=height,
        display_name=metadata.get('display_name'),
        scroll_direction=metadata.get('scroll_direction', 'none'),
        scroll_speed=metadata.get('scroll_speed', 0)
    )

    db.session.add(db_image)
    db.session.commit()

    if future:
        try:
            future.result()
        except Exception as e:
            # Rollback DB if file save fails asynchronously
            # We catch generic Exception because future.result() can raise anything
            # But we should be careful about what we swallow. Here we re-raise.
            try:
                db.session.delete(db_image)
                db.session.commit()
            except Exception:
                # If rollback fails, we log it (if we had a logger) or just pass
                # simpler to let the original exception propagate but try to cleanup
                pass
            raise e

    return db_image

def resize_image_to_display(pil_image, display_config, scroll_direction='none', scroll_speed=0):
    """
    Resizes an image to fit the display configuration.

    Args:
        pil_image: PIL Image object.
        display_config: Dictionary containing 'width', 'height', 'max_width', 'max_height'.
        scroll_direction: Direction of scrolling ('none', 'left', 'right', 'up', 'down').
        scroll_speed: Speed of scrolling.

    Returns:
        Resized PIL Image object (or original if no resize needed).
    """
    if not display_config:
        return pil_image

    width = pil_image.width
    height = pil_image.height

    d_width = display_config['width']
    d_height = display_config['height']

    scrolling = scroll_speed > 0 and scroll_direction != 'none'

    if not scrolling:
        # 1. If smaller (or equal) in both dimensions, keep size.
        if width <= d_width and height <= d_height:
            return pil_image

        # 2. Resize to fit within display dimensions
        # Use simple aspect ratio scaling to fit within d_width x d_height
        ratio = min(d_width / width, d_height / height)
        new_width = int(width * ratio)
        new_height = int(height * ratio)

        # Ensure dimensions are at least 1
        new_width = max(1, new_width)
        new_height = max(1, new_height)

        return pil_image.resize((new_width, new_height), resample=PILImage.NEAREST)

    else:
        # Scrolling enabled
        if scroll_direction in ['left', 'right']: # Horizontal
            # Non-scrolling side is height.
            if height > d_height:
                # Resize so height = d_height
                new_h = d_height
                # Aspect ratio: new_w / new_h = width / height => new_w = (width / height) * new_h
                new_w = int((width / height) * new_h)
                new_w = max(1, new_w)
                return pil_image.resize((new_w, new_h), resample=PILImage.NEAREST)
            return pil_image

        elif scroll_direction in ['up', 'down']: # Vertical
            # Non-scrolling side is width.
            if width > d_width:
                # Resize so width = d_width
                new_w = d_width
                # Aspect ratio: new_h = (height / width) * new_w
                new_h = int((height / width) * new_w)
                new_h = max(1, new_h)
                return pil_image.resize((new_w, new_h), resample=PILImage.NEAREST)
            return pil_image

    return pil_image
