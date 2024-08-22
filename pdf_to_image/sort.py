from flask import Blueprint, request, send_file
import fitz
import os
import zipfile
import logging
import shutil

logging.basicConfig(level=logging.DEBUG)

sort_bp = Blueprint('sort', __name__)

STATIC_DIR = os.path.join(os.getcwd(), 'pdf_to_image', 'static')

# Ensure the static directory exists
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

@sort_bp.route('/sort', methods=['POST'])
def sort_pages():
    file = request.files['file']
    sorted_pages = request.form['sorted_pages']  # This will be a comma-separated string of page numbers
    output_dir = os.path.join(STATIC_DIR, 'sort')

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    try:
        logging.debug(f"Processing file: {file.filename}")
        pdf = fitz.open(stream=file.read(), filetype='pdf')

        output_pdf = fitz.open()

        sorted_pages = [int(page) - 1 for page in sorted_pages.split(',')]

        for page in sorted_pages:
            output_pdf.insert_pdf(pdf, from_page=page, to_page=page)

        output_path = os.path.join(output_dir, 'sorted_pages.pdf')
        output_pdf.save(output_path)
        output_pdf.close()
        pdf.close()
        logging.debug(f"Created sorted PDF: {output_path}")

    except Exception as e:
        logging.error(f"Error sorting pages in PDF: {e}")
        return {"error": str(e)}, 500

    return send_file(output_path, as_attachment=True)
