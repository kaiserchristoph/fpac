from flask import Blueprint, url_for, current_app, redirect
from models import Image
import os
from PIL import Image as PILImage

api_bp = Blueprint('api', __name__)

@api_bp.route('/images')
def api_list_images():
    images = Image.query.all()
    image_list = []
    for img in images:
        image_list.append({
            'id': img.id,
            'filename': img.filename,
            'width': img.width,
            'height': img.height,
            'url': url_for('static', filename='uploads/' + img.filename, _external=True),
            'display_name': img.display_name,
            'scroll_direction': img.scroll_direction,
            'scroll_speed': img.scroll_speed
        })
    return {'images': image_list}

@api_bp.route('/download/<int:image_id>')
def api_download_image(image_id):
    img = Image.query.get_or_404(image_id)
    return redirect(url_for('static', filename='uploads/' + img.filename))

@api_bp.route('/image/<int:image_id>/rgb')
def api_get_image_rgb(image_id):
    img = Image.query.get_or_404(image_id)
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], img.filename)
    try:
        image = PILImage.open(filepath)
        if image.mode != 'RGB':
            image = image.convert('RGB')

        pixels = list(image.getdata())

        return {
            'width': image.width,
            'height': image.height,
            'display_name': img.display_name,
            # Return scrolling configuration for display client
            'scroll_direction': img.scroll_direction,
            'scroll_speed': img.scroll_speed,
            'pixels': pixels
        }
    except Exception as e:
        return {'error': str(e)}, 500
