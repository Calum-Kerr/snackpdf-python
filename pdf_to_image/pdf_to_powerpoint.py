from flask import Blueprint, request, send_file, jsonify, render_template
from pdf2pptx import convert_pdf2pptx
import os
import tempfile
import json
import traceback
from pdf2image import convert_from_path
import pytesseract

pdf_to_pptx_bp = Blueprint('pdf_to_pptx', __name__)

STATIC_DIR = os.path.join(os.getcwd(), 'pdf_to_image', 'static')

def sanitize_options(options):
    """Ensures all options are of the correct type."""
    sanitized = {}
    sanitized['dpi'] = int(options.get('dpi', 300))
    sanitized['output_format'] = options.get('output_format', 'pptx')
    return sanitized

def convert_pdf_to_pptx(pdf_path, pptx_path, options=None):
    if options is None:
        options = {}
    
    sanitized_options = sanitize_options(options)
    
    print("PDF to PowerPoint conversion options:", sanitized_options)

    try:
        convert_pdf2pptx(pdf_path, pptx_path, dpi=sanitized_options['dpi'])
    except Exception as e:
        print("Error during PDF to PowerPoint conversion:")
        traceback.print_exc()
        raise e

def ocr_pdf(pdf_path):
    pages = convert_from_path(pdf_path)
    text = ""
    for page in pages:
        text += pytesseract.image_to_string(page)
    return text

@pdf_to_pptx_bp.route('/pdf_to_pptx', methods=['POST'])
def pdf_to_pptx():
    try:
        print("Received request to /pdf_to_pptx")
        file = request.files['file']
        options = json.loads(request.form.get('options', '{}'))
        print(f"Options received: {options}")

        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = os.path.join(temp_dir, file.filename)
            file.save(pdf_path)
            print(f"PDF saved to {pdf_path}")
            
            pptx_path = os.path.splitext(pdf_path)[0] + '.pptx'
            
            if options.get('use_ocr', False):
                ocr_text = ocr_pdf(pdf_path)
                print(f"OCR text generated: {ocr_text[:100]}...")
            
            convert_pdf_to_pptx(pdf_path, pptx_path, options)
            print(f"PDF converted to PowerPoint at {pptx_path}")
            
            return send_file(pptx_path, as_attachment=True, download_name=f'{os.path.splitext(file.filename)[0]}.pptx', mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation')

    except Exception as e:
        print("Error occurred during /pdf_to_pptx request:")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@pdf_to_pptx_bp.route('/pdf_to_pptx_page')
def pdf_to_pptx_page():
    return render_template('pdf_to_pptx.html')