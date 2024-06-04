# pdf_to_image/__init__.py
from flask import Flask, render_template, jsonify

# Add new tools.py files
from .convert import convert_bp
from .panoramic import panoramic_bp
from .compress import compress_bp

import traceback

def create_app():
    app = Flask(__name__)
    
    # Register blueprints
    app.register_blueprint(convert_bp)
    app.register_blueprint(panoramic_bp)
    app.register_blueprint(compress_bp)
    
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.errorhandler(Exception)
    def handle_exception(e):
        # Print the traceback to the console
        traceback.print_exc()
        response = {
            "error": str(e),
            "traceback": traceback.format_exc()
        }
        return jsonify(response), 500

    return app
