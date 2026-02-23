import base64
import io
from flask import Blueprint, render_template, request, current_app, redirect, url_for, flash
from flask_login import login_required, current_user
from PIL import Image as PILImage
from PIL import UnidentifiedImageError
from sqlalchemy.exc import SQLAlchemyError
from utils import save_image_artifact

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html', displays=current_app.config.get('DISPLAYS', []))

@main_bp.route('/draw')
@login_required
def draw():
    return render_template('draw.html', displays=current_app.config.get('DISPLAYS', []))

@main_bp.route('/save_drawing', methods=['POST'])
@login_required
def save_drawing():
    data = request.get_json()
    image_data = data['image']
    display_name = data.get('display_name')
    scroll_direction = data.get('scroll_direction', 'none')
    scroll_speed = data.get('scroll_speed', 0)

    # Remove header of data URL
    image_data = image_data.replace('data:image/png;base64,', '')
    image_bytes = base64.b64decode(image_data)

    # Save as BMP
    try:
        image = PILImage.open(io.BytesIO(image_bytes))

        save_image_artifact(
            pil_image=image,
            user_id=current_user.id,
            upload_folder=current_app.config['UPLOAD_FOLDER'],
            filename_prefix="drawing_",
            metadata={
                'display_name': display_name,
                'scroll_direction': scroll_direction,
                'scroll_speed': scroll_speed
            },
            executor=current_app.executor
        )

        return {'success': True}
    except UnidentifiedImageError as e:
        current_app.logger.error(f"Invalid image format: {e}")
        return {'success': False, 'error': 'Invalid image format'}
    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error: {e}")
        return {'success': False, 'error': 'Database error'}
    except (OSError, IOError) as e:
        current_app.logger.error(f"File save error: {e}")
        return {'success': False, 'error': 'File save error'}
    except Exception as e:
        current_app.logger.error(f"Unexpected error: {e}")
        return {'success': False, 'error': 'An unexpected error occurred'}

@main_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file:
            try:
                image = PILImage.open(file)

                save_image_artifact(
                    pil_image=image,
                    user_id=current_user.id,
                    upload_folder=current_app.config['UPLOAD_FOLDER'],
                    filename_prefix="upload_",
                    executor=None
                )

                flash('File uploaded successfully')
                return redirect(url_for('main.index'))
            except Exception as e:
                flash(f'Error uploading file: {e}')
                return redirect(request.url)
    return render_template('upload.html')
