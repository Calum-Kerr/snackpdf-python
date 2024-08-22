from flask import Blueprint, request, send_file
import fitz
import os
import logging
import shutil

logging.basicConfig(level=logging.DEBUG)

rotate_bp = Blueprint('rotate', __name__)

STATIC_DIR = os.path.join(os.getcwd(), 'pdf_to_image', 'static')

# Ensure the static directory exists
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

@rotate_bp.route('/rotate', methods=['POST'])
def rotate_pages():
    try:
        file = request.files['file']
        degrees = int(request.form['degrees'])  # Rotation degree (90, 180, or 270)
        pages_to_rotate = request.form['page_numbers']  # Comma separated string of page numbers
        output_dir = os.path.join(STATIC_DIR, 'rotate')

        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir, exist_ok=True)

        logging.debug(f"Processing file: {file.filename}")
        pdf = fitz.open(stream=file.read(), filetype='pdf')

        pages_to_rotate = [int(page) - 1 for page in pages_to_rotate.split(',')]

        for page_num in pages_to_rotate:
            page = pdf[page_num]
            page.set_rotation(page.rotation + degrees)

        output_path = os.path.join(output_dir, 'rotated_pages.pdf')
        pdf.save(output_path)
        pdf.close()
        logging.debug(f"Created rotated PDF: {output_path}")

    except Exception as e:
        logging.error(f"Error rotating pages in PDF: {e}")
        return {"error": str(e)}, 500

    return send_file(output_path, as_attachment=True)

