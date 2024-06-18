from flask import Flask, render_template, jsonify
from .convert import convert_bp
from .panoramic import panoramic_bp
from .compress import compress_bp
from .pdf_to_word import pdf_to_word_bp
from .pdf_to_powerpoint import pdf_to_powerpoint_bp
from .merge import merge_bp
from .split import split_bp
#from .convert_to_pdf import convert_to_pdf_bp
#from .convert_from_pdf import convert_from_pdf_bp
#from .organize import organize_bp
#from .optimise import optimise_bp
#from .edit import edit_bp
#from .security import security_bp
#from .ocr import ocr_bp
#from .batch import batch_bp
#from .annotate import annotate_bp
#from .form import form_bp
import traceback

def create_app():
    app = Flask(__name__)

    # Register blueprints
    app.register_blueprint(convert_bp)
    app.register_blueprint(panoramic_bp)
    app.register_blueprint(compress_bp)
    app.register_blueprint(pdf_to_word_bp)
    app.register_blueprint(pdf_to_powerpoint_bp)
    app.register_blueprint(merge_bp)
    app.register_blueprint(split_bp)
    #app.register_blueprint(convert_to_pdf_bp)
    #app.register_blueprint(convert_from_pdf_bp)
    #app.register_blueprint(optimise_bp)
    #app.register_blueprint(organize_bp)
    #app.register_blueprint(edit_bp)
    #app.register_blueprint(security_bp)
    #app.register_blueprint(ocr_bp)
    #app.register_blueprint(batch_bp)
    #app.register_blueprint(annotate_bp)
    #app.register_blueprint(form_bp)

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
