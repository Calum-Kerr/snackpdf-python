from flask import Flask, render_template, jsonify, send_from_directory
import traceback
import os

def create_app():
    app = Flask(__name__)

    # Register blueprints for convert-to-PDF functionality (Agent 2)
    try:
        from .convert_to_pdf import convert_to_pdf_bp
        from .office_to_pdf import office_to_pdf_bp
        from .html_to_pdf import html_to_pdf_bp

        app.register_blueprint(convert_to_pdf_bp)
        app.register_blueprint(office_to_pdf_bp)
        app.register_blueprint(html_to_pdf_bp)
    except ImportError as e:
        print(f"Warning: Could not import convert-to-PDF blueprints: {e}")
        # Continue without blueprints for development

    # Register blueprints for PDF Content Editing Tools (Agent 3)
    try:
        from .watermark import watermark_bp
        from .page_numbers import page_numbers_bp
        from .edit_content import edit_content_bp
        from .redact import redact_bp

        app.register_blueprint(watermark_bp)
        app.register_blueprint(page_numbers_bp)
        app.register_blueprint(edit_content_bp)
        app.register_blueprint(redact_bp)
    except ImportError as e:
        print(f"Warning: Could not import PDF editing blueprints: {e}")
        # Continue without blueprints for now

    # Register blueprints for PDF Optimization Tools (Agent 1)
    try:
        from .compress import compress_bp
        from .repair import repair_bp

        app.register_blueprint(compress_bp)
        app.register_blueprint(repair_bp)
    except ImportError as e:
        print(f"Warning: Could not import optimization blueprints: {e}")
        # Continue without blueprints for now

    # Register blueprints for PDF Organization Tools (Agent 4)
    try:
        from .sort import sort_bp
        from .rotate import rotate_bp
        # split and merge blueprints already exist in the base system

        app.register_blueprint(sort_bp)
        app.register_blueprint(rotate_bp)
    except ImportError as e:
        print(f"Warning: Could not import organization blueprints: {e}")
        # Continue without blueprints for now

    # Register blueprints for PDF Conversion Tools (Agent 5)
    try:
        from .pdf_to_excel import pdf_to_excel_bp
        from .pdf_to_pdfa import pdf_to_pdfa_bp
        # Other conversion tools already exist in base system

        app.register_blueprint(pdf_to_excel_bp)
        app.register_blueprint(pdf_to_pdfa_bp)
    except ImportError as e:
        print(f"Warning: Could not import conversion blueprints: {e}")
        # Continue without blueprints for now

    # Register blueprints for PDF Security Tools (Agent 6)
    try:
        from .security import security_bp

        app.register_blueprint(security_bp)
    except ImportError as e:
        print(f"Warning: Could not import security blueprints: {e}")
        # Continue without blueprints for now

    # Register blueprint for basic operations (core functionality)
    try:
        from .basic_operations import basic_operations_bp

        app.register_blueprint(basic_operations_bp)
    except ImportError as e:
        print(f"Warning: Could not import basic operations blueprint: {e}")
        # Continue without blueprint for now


    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/pdf_to_jpg')
    def pdf_to_jpg():
        return render_template('pdf_to_jpg_new.html')

    @app.route('/pdf_to_panoramic')
    def pdf_to_panoramic():
        return render_template('pdf_to_panoramic_new.html')

    @app.route('/compress')
    def compress():
        return render_template('compress_new.html')
        
    @app.route('/merge')
    def merge():
        return render_template('merge_new.html')

    @app.route('/split')
    def split():
        return render_template('split_new.html')

    @app.route('/remove')
    def remove():
        return render_template('remove_new.html')

    @app.route('/extract')
    def extract():
        return render_template('extract_new.html')

    @app.route('/sort')
    def sort():
        return render_template('sort_new.html')

    @app.route('/rotate')
    def rotate():
        return render_template('rotate_new.html')

    @app.route('/word')
    def word():
        return render_template('word_new.html')

    @app.route('/powerpoint')
    def powerpoint():
        return render_template('powerpoint_new.html')

    @app.route('/repair')
    def repair():
        return render_template('repair_new.html')

    @app.route('/ocr')
    def ocr():
        return render_template('ocr_new.html')

    @app.route('/page_numbers')
    def page_numbers():
        return render_template('page_numbers_new.html')

    @app.route('/watermark')
    def watermark():
        return render_template('watermark_new.html')

    # New pages routes
    @app.route('/jpg_to_pdf')
    def jpg_to_pdf():
        return render_template('jpg_to_pdf_new.html')

    @app.route('/word_to_pdf')
    def word_to_pdf():
        return render_template('word_to_pdf_new.html')

    @app.route('/powerpoint_to_pdf')
    def powerpoint_to_pdf():
        return render_template('powerpoint_to_pdf_new.html')

    @app.route('/excel_to_pdf')
    def excel_to_pdf():
        return render_template('excel_to_pdf_new.html')

    @app.route('/html_to_pdf')
    def html_to_pdf():
        return render_template('html_to_pdf_new.html')

    @app.route('/zip_to_pdf')
    def zip_to_pdf():
        return render_template('zip_to_pdf_new.html')

    @app.route('/edit_content')
    def edit_content():
        return render_template('edit_content_new.html')

    @app.route('/pdf_to_excel')
    def pdf_to_excel():
        return render_template('pdf_to_excel_new.html')

    @app.route('/pdf_to_pdfa')
    def pdf_to_pdfa():
        return render_template('pdf_to_pdfa_new.html')

    @app.route('/unlock')
    def unlock():
        return render_template('unlock_new.html')

    @app.route('/protect')
    def protect():
        return render_template('protect_new.html')

    @app.route('/sign')
    def sign():
        return render_template('sign_new.html')

    @app.route('/compare')
    def compare():
        return render_template('compare_new.html')

    @app.route('/redact')
    def redact():
        return render_template('redact_new.html')

    @app.route('/flatten')
    def flatten():
        return render_template('flatten_new.html')

    # Essential Pages Routes
    @app.route('/privacy')
    def privacy():
        return render_template('privacy.html')

    @app.route('/terms')
    def terms():
        return render_template('terms.html')

    @app.route('/about')
    def about():
        return render_template('about.html')

    # SEO Routes
    @app.route('/sitemap.xml')
    def sitemap():
        return send_from_directory(os.path.dirname(os.path.dirname(__file__)), 'sitemap.xml', mimetype='application/xml')

    @app.route('/robots.txt')
    def robots():
        return send_from_directory(os.path.dirname(os.path.dirname(__file__)), 'robots.txt', mimetype='text/plain')

    # Google AdSense ads.txt
    @app.route('/ads.txt')
    def ads_txt():
        from flask import Response
        ads_content = "google.com, pub-3309044253592353, DIRECT, f08c47fec0942fa0"
        return Response(ads_content, mimetype='text/plain')

    # Ghostscript test endpoint
    @app.route('/test-ghostscript')
    def test_ghostscript():
        from flask import Response
        try:
            from .ghostscript_utils import test_ghostscript
            success = test_ghostscript()
            if success:
                return Response("✅ Ghostscript is working properly!", mimetype='text/plain')
            else:
                return Response("❌ Ghostscript test failed", mimetype='text/plain'), 500
        except Exception as e:
            return Response(f"❌ Ghostscript error: {str(e)}", mimetype='text/plain'), 500

    # Google Search Console Verification
    @app.route('/google6520a768170937d3.html')
    def google_verification():
        return send_from_directory(os.path.dirname(os.path.dirname(__file__)), 'google6520a768170937d3.html', mimetype='text/html')

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
