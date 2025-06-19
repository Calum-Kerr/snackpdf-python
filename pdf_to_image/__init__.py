from flask import Flask, render_template, jsonify
import traceback

def create_app():
    app = Flask(__name__)

    # Blueprints temporarily disabled for initial deployment
    # Will be re-enabled once proper dependencies are added


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

    @app.route('/powerpoint')
    def powerpoint():
        return render_template('powerpoint.html')

    @app.route('/repair')
    def repair():
        return render_template('repair.html')

    @app.route('/ocr')
    def ocr():
        return render_template('ocr.html')

    @app.route('/page_numbers')
    def page_numbers():
        return render_template('page_numbers.html')

    @app.route('/watermark')
    def watermark():
        return render_template('watermark.html')

    # New pages routes
    @app.route('/jpg_to_pdf')
    def jpg_to_pdf():
        return render_template('jpg_to_pdf.html')

    @app.route('/word_to_pdf')
    def word_to_pdf():
        return render_template('word_to_pdf.html')

    @app.route('/powerpoint_to_pdf')
    def powerpoint_to_pdf():
        return render_template('powerpoint_to_pdf.html')

    @app.route('/excel_to_pdf')
    def excel_to_pdf():
        return render_template('excel_to_pdf.html')

    @app.route('/html_to_pdf')
    def html_to_pdf():
        return render_template('html_to_pdf.html')

    @app.route('/zip_to_pdf')
    def zip_to_pdf():
        return render_template('zip_to_pdf.html')

    @app.route('/edit_content')
    def edit_content():
        return render_template('edit_content.html')

    @app.route('/pdf_to_excel')
    def pdf_to_excel():
        return render_template('pdf_to_excel.html')

    @app.route('/pdf_to_pdfa')
    def pdf_to_pdfa():
        return render_template('pdf_to_pdfa.html')

    @app.route('/unlock')
    def unlock():
        return render_template('unlock.html')

    @app.route('/protect')
    def protect():
        return render_template('protect.html')

    @app.route('/sign')
    def sign():
        return render_template('sign.html')

    @app.route('/compare')
    def compare():
        return render_template('compare.html')

    @app.route('/redact')
    def redact():
        return render_template('redact.html')

    @app.route('/flatten')
    def flatten():
        return render_template('flatten.html')



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
