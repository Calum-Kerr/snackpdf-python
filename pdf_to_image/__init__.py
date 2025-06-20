from flask import Flask, render_template, jsonify, send_from_directory
import traceback
import os

def create_app():
    app = Flask(__name__)

    # Import and register blueprints for PDF conversion tools
    blueprints_to_register = [
        ('convert', 'convert_bp'),
        ('pdf_to_excel', 'pdf_to_excel_bp'),
        ('pdf_to_pdfa', 'pdf_to_pdfa_bp'),
    ]

    # Try to import optional blueprints
    optional_blueprints = [
        ('pdf_to_word', 'pdf_to_word_bp'),
        ('pdf_to_powerpoint', 'pdf_to_powerpoint_bp'),
    ]

    for module_name, blueprint_name in blueprints_to_register:
        try:
            module = __import__(f'pdf_to_image.{module_name}', fromlist=[blueprint_name])
            blueprint = getattr(module, blueprint_name)
            app.register_blueprint(blueprint)
            print(f"Successfully registered {blueprint_name}")
        except Exception as e:
            print(f"Warning: Could not import {blueprint_name}: {e}")

    for module_name, blueprint_name in optional_blueprints:
        try:
            module = __import__(f'pdf_to_image.{module_name}', fromlist=[blueprint_name])
            blueprint = getattr(module, blueprint_name)
            app.register_blueprint(blueprint)
            print(f"Successfully registered {blueprint_name}")
        except Exception as e:
            print(f"Info: Optional blueprint {blueprint_name} not available: {e}")


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
