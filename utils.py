import os
from datetime import datetime, timezone
from extensions import db
from models import Image

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
