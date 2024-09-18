from flask import Blueprint, request, send_file, jsonify
import fitz  # PyMuPDF
import os
import logging
import shutil

repair_bp = Blueprint('repair', __name__)

STATIC_DIR = os.path.join(os.getcwd(), 'pdf_to_image', 'static')

# Ensure the static directory exists
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

@repair_bp.route('/repair', methods=['POST'])
def repair_pdf():
    file = request.files['file']
    output_dir = os.path.join(STATIC_DIR, 'repair')

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    try:
        # Try to open the PDF
        logging.debug(f"Processing file: {file.filename}")
        pdf = fitz.open(stream=file.read(), filetype='pdf')
    except Exception as e:
        logging.error(f"Error opening PDF: {e}")
        return jsonify({"error": "Failed to open PDF, it may be corrupt"}), 500

    try:
        # Rebuild the PDF page by page
        output_pdf = fitz.open()
        for page_number in range(pdf.page_count):
            try:
                page = pdf.load_page(page_number)
                output_pdf.insert_pdf(pdf, from_page=page_number, to_page=page_number)
            except Exception as e:
                logging.error(f"Failed to process page {page_number + 1}: {e}")
                continue

        output_path = os.path.join(output_dir, f'repaired_{file.filename}')
        output_pdf.save(output_path)
        output_pdf.close()
        pdf.close()
        logging.debug(f"Repaired PDF saved: {output_path}")

    except Exception as e:
        logging.error(f"Error repairing PDF: {e}")
        return jsonify({"error": "Failed to repair PDF"}), 500

    return send_file(output_path, as_attachment=True)

