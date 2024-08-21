from flask import Blueprint, request, send_file, jsonify, url_for
import fitz
import os
import logging

logging.basicConfig(level=logging.DEBUG)

merge_bp = Blueprint('merge', __name__)

STATIC_DIR = os.path.join(os.getcwd(), 'pdf_to_image', 'static')

# Ensure the static directory exists
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

@merge_bp.route('/merge', methods=['POST'])
def merge_pdfs():
    files = request.files.getlist('files')
    output_filename = request.form.get('output_filename', 'merged.pdf')

    if not output_filename.endswith('.pdf'):
        output_filename += '.pdf'

    output_path = os.path.join(STATIC_DIR, output_filename)

    if os.path.exists(output_path):
        os.remove(output_path)
    merged_document = fitz.open()

    try:
        for file in files:
            logging.debug(f"Processing file: {file.filename}")
            pdf = fitz.open(stream=file.read(), filetype='pdf')
            merged_document.insert_pdf(pdf)

        merged_document.save(output_path)
        merged_document.close()
        logging.debug(f"Merged PDF saved to: {output_path}")
    except Exception as e:
        logging.error(f"Error merging PDFs: {e}")
        return {"error": str(e)}, 500

    return send_file(output_path, as_attachment=True)

