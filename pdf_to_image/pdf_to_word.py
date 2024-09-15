from flask import Blueprint, request, send_file, jsonify, render_template
from pdf2docx import Converter
import os
import tempfile
import json
from docx import Document
import pytesseract
from pdf2image import convert_from_path
import traceback  # Import for detailed error reporting

pdf_to_word_bp = Blueprint('pdf_to_word', __name__)

STATIC_DIR = os.path.join(os.getcwd(), 'pdf_to_image', 'static')

def sanitize_options(options):
    """Ensures all options are of the correct type."""
    sanitized = {}
    sanitized['default_font_size'] = int(options.get('default_font_size', 11))  # Ensure this is int
    sanitized['line_height'] = float(options.get('line_height', 1.15))  # Ensure this is float
    sanitized['default_font'] = options.get('default_font', 'Arial')
    sanitized['css_path'] = options.get('css_path', None)
    return sanitized

def convert_pdf_to_word(pdf_path, docx_path, options=None):
    if options is None:
        options = {}
    
    sanitized_options = sanitize_options(options)  # Use sanitized options
    
    # Log all layout_analysis_settings and docx_settings for debugging
    print("layout_analysis_settings:", {
        'debug': False,
        'curve_path_ratio': 0.7,
        'line_overlap_threshold': 0.9,
        'line_break_width_ratio': 0.1,
        'line_break_free_space_ratio': 0.3,
        'line_separate_threshold': int(5.0),
        'line_separate_length_ratio': 0.5,
        'line_separate_free_space_ratio': 0.1,
        'line_separate_free_space_factor': int(1.5),
    })

    print("docx_settings:", {
        'default_font': options.get('default_font', 'Arial'),
        'default_font_size': int(options.get('default_font_size', 11)),
        'line_height': float(options.get('line_height', 1.15)),  # Keeping this as float
        'css_path': options.get('css_path', None),
    })

    try:
        cv = Converter(pdf_path)
        cv.convert(docx_path, 
            layout_analysis_settings={
                'curve_path_ratio': float(0.7),
                'line_overlap_threshold': float(0.9),
                'line_break_width_ratio': float(0.1),
                'line_break_free_space_ratio': float(0.3),
                'line_separate_threshold': int(5),  # Ensure this is int
                'line_separate_length_ratio': float(0.5),
                'line_separate_free_space_ratio': float(0.1),
                'line_separate_free_space_factor': int(1),  # Cast float to int if necessary
            },
            docx_settings={
                'default_font': sanitized_options['default_font'],
                'default_font_size': sanitized_options['default_font_size'],
                'line_height': sanitized_options['line_height'],  # Ensured to be float
                'css_path': sanitized_options['css_path'],
            })
        cv.close()

    except Exception as e:
        # Capture and print the full traceback for more details
        print("Error during PDF to Word conversion:")
        traceback.print_exc()  # Prints the full traceback
        raise e  # Re-raise the exception to let it propagate

def ocr_pdf(pdf_path):
    pages = convert_from_path(pdf_path)
    text = ""
    for page in pages:
        text += pytesseract.image_to_string(page)
    return text

@pdf_to_word_bp.route('/pdf_to_word', methods=['POST'])
def pdf_to_word():
    try:
        print("Received request to /pdf_to_word")  # Log request receipt
        file = request.files['file']
        options = json.loads(request.form.get('options', '{}'))
        print(f"Options received: {options}")  # Log options

        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = os.path.join(temp_dir, file.filename)
            file.save(pdf_path)
            print(f"PDF saved to {pdf_path}")  # Log saved PDF location
            
            docx_path = os.path.splitext(pdf_path)[0] + '.docx'
            
            if options.get('use_ocr', False):
                ocr_text = ocr_pdf(pdf_path)
                print(f"OCR text generated: {ocr_text[:100]}...")  # Log partial OCR result
            
            convert_pdf_to_word(pdf_path, docx_path, options)
            print(f"PDF converted to Word at {docx_path}")  # Log conversion success
            
            return send_file(docx_path, as_attachment=True, download_name=f'{os.path.splitext(file.filename)[0]}.docx', mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')

    except Exception as e:
        print("Error occurred during /pdf_to_word request:")
        traceback.print_exc()  # Print the full traceback for debugging
        return jsonify({"error": str(e)}), 500

@pdf_to_word_bp.route('/pdf_to_word_page')
def pdf_to_word_page():
    return render_template('pdf_to_word.html')
