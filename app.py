import os
import json
import concurrent.futures

from flask import Flask
from extensions import db, login_manager
from blueprints.auth import auth_bp
from blueprints.main import main_bp
from blueprints.api import api_bp

def create_app(test_config=None):
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB limit

    # Load displays configuration
    displays_path = os.path.join(os.path.dirname(__file__), 'displays.json')
    if os.path.exists(displays_path):
        with open(displays_path, 'r') as f:
            app.config['DISPLAYS'] = json.load(f)
    else:
        app.config['DISPLAYS'] = []

    if test_config:
        app.config.update(test_config)

    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # ThreadPoolExecutor for offloading I/O tasks
    app.executor = concurrent.futures.ThreadPoolExecutor()

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    # Only enable debug mode if FLASK_DEBUG is explicitly set to a truthy value
    debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() in ['true', '1', 't']
    app.run(host='0.0.0.0', debug=debug_mode)
