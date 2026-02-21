import base64
import io
import os
from datetime import datetime

from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from PIL import Image as PILImage

from extensions import db, login_manager
from models import User, Image

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
    
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    with app.app_context():
        db.create_all()

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            if User.query.filter_by(username=username).first():
                flash('Username already exists')
                return redirect(url_for('register'))
            user = User(username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('Registration successful')
            return redirect(url_for('login'))
        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            user = User.query.filter_by(username=username).first()
            if user is None or not user.check_password(password):
                flash('Invalid username or password')
                return redirect(url_for('login'))
            login_user(user)
            return redirect(url_for('index'))
        return render_template('login.html')

    @app.route('/logout')
    def logout():
        logout_user()
        return redirect(url_for('index'))

    @app.route('/draw')
    @login_required
    def draw():
        return render_template('draw.html')

    @app.route('/save_drawing', methods=['POST'])
    @login_required
    def save_drawing():
        data = request.get_json()
        image_data = data['image']
        
        # Remove header of data URL
        image_data = image_data.replace('data:image/png;base64,', '')
        image_bytes = base64.b64decode(image_data)
        
        # Save as BMP
        try:
            image = PILImage.open(io.BytesIO(image_bytes))
            filename = f"drawing_{current_user.id}_{int(datetime.utcnow().timestamp())}.bmp"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(filepath, 'BMP')
            
            # Save to DB
            db_image = Image(filename=filename, user_id=current_user.id, width=image.width, height=image.height)
            db.session.add(db_image)
            db.session.commit()
            
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @app.route('/upload', methods=['GET', 'POST'])
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
                    # Convert to RGB to avoid issues with transparency or different modes
                    if image.mode != 'RGB':
                        image = image.convert('RGB')
                        
                    filename = f"upload_{current_user.id}_{int(datetime.utcnow().timestamp())}.bmp"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    image.save(filepath, 'BMP')
                    
                    db_image = Image(filename=filename, user_id=current_user.id, width=image.width, height=image.height)
                    db.session.add(db_image)
                    db.session.commit()
                    
                    flash('File uploaded successfully')
                    return redirect(url_for('index'))
                except Exception as e:
                    flash(f'Error uploading file: {e}')
                    return redirect(request.url)
        return render_template('upload.html')

    @app.route('/api/images')
    def api_list_images():
        images = Image.query.all()
        image_list = []
        for img in images:
            image_list.append({
                'id': img.id,
                'filename': img.filename,
                'width': img.width,
                'height': img.height,
                'url': url_for('static', filename='uploads/' + img.filename, _external=True)
            })
        return {'images': image_list}

    @app.route('/api/download/<int:image_id>')
    def api_download_image(image_id):
        img = Image.query.get_or_404(image_id)
        return redirect(url_for('static', filename='uploads/' + img.filename))

    @app.route('/api/image/<int:image_id>/rgb')
    def api_get_image_rgb(image_id):
        img = Image.query.get_or_404(image_id)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], img.filename)
        try:
            image = PILImage.open(filepath)
            if image.mode != 'RGB':
                image = image.convert('RGB')

            pixels = list(image.getdata())
            # Convert list of tuples to list of lists
            pixels_list = [list(p) for p in pixels]

            return {
                'width': image.width,
                'height': image.height,
                'pixels': pixels_list
            }
        except Exception as e:
            return {'error': str(e)}, 500

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', debug=True)
