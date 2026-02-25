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

def resize_image_to_display(pil_image, display_config, scroll_direction='none'):
    """
    Resizes an image to fit the display configuration, considering scroll direction.

    Args:
        pil_image: PIL Image object.
        display_config: Dictionary containing 'width', 'height', 'max_width', 'max_height'.
        scroll_direction: Direction of scrolling ('none', 'left', 'right', 'up', 'down').

    Returns:
        Resized PIL Image object (or original if no resize needed).
    """
    if not display_config:
        return pil_image

    width = pil_image.width
    height = pil_image.height

    d_width = display_config['width']
    d_height = display_config['height']
    d_max_width = display_config.get('max_width', d_width)
    d_max_height = display_config.get('max_height', d_height)

    # Logic for non-scrolling or speed=0 (handled by caller passing 'none')
    if scroll_direction == 'none':
        # 1. If smaller (or equal) in both dimensions, keep size.
        if width <= d_width and height <= d_height:
            return pil_image

        # 2. Calculate potential scales and resulting dimensions
        candidates = []

        # Option A: Fix Width to Display Width
        scale_w = d_width / width
        new_h_from_w = int(height * scale_w)
        if new_h_from_w <= d_max_height:
            candidates.append((scale_w, (d_width, new_h_from_w)))

        # Option B: Fix Height to Display Height
        scale_h = d_height / height
        new_w_from_h = int(width * scale_h)
        if new_w_from_h <= d_max_width:
            candidates.append((scale_h, (new_w_from_h, d_height)))

        if candidates:
            best_candidate = max(candidates, key=lambda x: x[0])
            new_size = best_candidate[1]
            return pil_image.resize(new_size, resample=PILImage.NEAREST)

        return pil_image

    elif scroll_direction in ['left', 'right']:
        # Horizontal scroll: Fit height to display height. Width scales proportionally.
        # But if width ends up > max_width, we must cap it.

        # If height <= d_height, we might not resize?
        # But for scrolling, usually we want to fill the height.
        # Let's assume standard behavior: Scale to fit height.

        scale = d_height / height
        new_width = int(width * scale)
        new_height = d_height

        # Check max width constraint (if it's intended as a hard limit for any image)
        if new_width > d_max_width:
            scale_limit = d_max_width / new_width
            new_width = d_max_width
            new_height = int(new_height * scale_limit)

        if (new_width, new_height) != (width, height):
            return pil_image.resize((new_width, new_height), resample=PILImage.NEAREST)

    elif scroll_direction in ['up', 'down']:
        # Vertical scroll: Fit width to display width. Height scales.
        scale = d_width / width
        new_width = d_width
        new_height = int(height * scale)

        if new_height > d_max_height:
             scale_limit = d_max_height / new_height
             new_height = d_max_height
             new_width = int(new_width * scale_limit)

        if (new_width, new_height) != (width, height):
            return pil_image.resize((new_width, new_height), resample=PILImage.NEAREST)

    return pil_image
