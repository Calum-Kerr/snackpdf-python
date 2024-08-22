from flask import Blueprint, request, send_file
import fitz  # PyMuPDF
import os
import logging

remove_bp = Blueprint('remove', __name__)

STATIC_DIR = os.path.join(os.getcwd(), 'pdf_to_image', 'static')

# Ensure the static directory exists
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

@remove_bp.route('/remove', methods=['POST'])
def remove_pages():
    file = request.files['file']
    page_numbers = request.form['page_numbers']

    try:
        logging.debug(f"Processing file: {file.filename}")
        pdf = fitz.open(stream=file.read(), filetype='pdf')

        output_pdf = fitz.open()
        pages_to_remove = list(map(int, page_numbers.split(',')))

        for i in range(pdf.page_count):
            if (i + 1) not in pages_to_remove:  # Page numbers are 1-indexed
                output_pdf.insert_pdf(pdf, from_page=i, to_page=i)

        output_path = os.path.join(STATIC_DIR, 'removed_pages.pdf')
        output_pdf.save(output_path)
        output_pdf.close()
        logging.debug(f"Created PDF with removed pages: {output_path}")
    except Exception as e:
        logging.error(f"Error removing pages: {e}")
        return {"error": str(e)}, 500

    return send_file(output_path, as_attachment=True)
