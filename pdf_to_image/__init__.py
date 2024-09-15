from flask import Flask, render_template, jsonify
from .convert import convert_bp
from .panoramic import panoramic_bp
from .compress import compress_bp
from .pdf_to_word import pdf_to_word_bp
from .merge import merge_bp
from .split import split_bp
from .remove import remove_bp
from .extract import extract_bp
from .sort import sort_bp
from .rotate import rotate_bp
from .convert_to_pdf import convert_to_pdf_bp
from .security import security_bp
import traceback

def create_app():
    app = Flask(__name__)

    # Register blueprints
    app.register_blueprint(convert_bp)
    app.register_blueprint(panoramic_bp)
    app.register_blueprint(compress_bp)
    app.register_blueprint(pdf_to_word_bp)
    app.register_blueprint(merge_bp)
    app.register_blueprint(split_bp)
    app.register_blueprint(convert_to_pdf_bp)
    app.register_blueprint(security_bp)
    app.register_blueprint(remove_bp)
    app.register_blueprint(extract_bp)
    app.register_blueprint(sort_bp)
    app.register_blueprint(rotate_bp)

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/pdf_to_jpg')
    def pdf_to_jpg():
        return render_template('pdf_to_jpg.html')

    @app.route('/pdf_to_panoramic')
    def pdf_to_panoramic():
        return render_template('pdf_to_panoramic.html')

    @app.route('/compress')
    def compress():
        return render_template('compress.html')
        
    @app.route('/merge')
    def merge():
        return render_template('merge.html')

    @app.route('/split')
    def split():
        return render_template('split.html')

    @app.route('/remove')
    def remove():
        return render_template('remove.html')

    @app.route('/extract')
    def extract():
        return render_template('extract.html')

    @app.route('/sort')
    def sort():
        return render_template('sort.html')

    @app.route('/rotate')
    def rotate():
        return render_template('rotate.html')

    @app.route('/word')
    def word():
        return render_template('word.html')

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
