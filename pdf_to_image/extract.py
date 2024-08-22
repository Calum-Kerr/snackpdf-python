from flask import Blueprint, request, send_file
import fitz
import os
import zipfile
import logging
import shutil

logging.basicConfig(level=logging.DEBUG)

extract_bp = Blueprint('extract', __name__)

STATIC_DIR = os.path.join(os.getcwd(), 'pdf_to_image', 'static')

# Ensure the static directory exists
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

@extract_bp.route('/extract', methods=['POST'])
def extract_pages():
    file = request.files['file']
    pages_to_extract = request.form['page_numbers']  # Changed from 'page_ranges' to 'page_numbers'
    output_dir = os.path.join(STATIC_DIR, 'extract')

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    try:
        logging.debug(f"Processing file: {file.filename}")
        pdf = fitz.open(stream=file.read(), filetype='pdf')

        output_pdf = fitz.open()

        pages_to_extract = sorted([int(page) - 1 for page in pages_to_extract.split(',')])

        for page in pages_to_extract:
            output_pdf.insert_pdf(pdf, from_page=page, to_page=page)

        output_path = os.path.join(output_dir, 'extracted_pages.pdf')
        output_pdf.save(output_path)
        output_pdf.close()
        pdf.close()
        logging.debug(f"Created extracted PDF: {output_path}")

    except Exception as e:
        logging.error(f"Error extracting pages from PDF: {e}")
        return {"error": str(e)}, 500

    return send_file(output_path, as_attachment=True)

