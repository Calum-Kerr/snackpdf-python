from flask import Blueprint, request, send_file, jsonify
import fitz  # PyMuPDF
import os
import logging
import shutil
import tempfile

page_numbers_bp = Blueprint('page_numbers', __name__)

STATIC_DIR = os.path.join(os.getcwd(), 'pdf_to_image', 'static')

# Ensure the static directory exists
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

@page_numbers_bp.route('/add_page_numbers', methods=['POST'])
def add_page_numbers():
    file = request.files['file']
    position = request.form.get('position', 'bottom_center')  # default to 'bottom_center'
    font_size = int(request.form.get('font_size', 12))
    output_dir = os.path.join(STATIC_DIR, 'page_numbers')

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    try:
        logging.debug(f"Processing file: {file.filename}")
        pdf = fitz.open(stream=file.read(), filetype='pdf')

        # Prepare the output PDF
        output_pdf = fitz.open()

        for page_number in range(pdf.page_count):
            page = pdf.load_page(page_number)
            rect = page.rect
            text = f"{page_number + 1}"  # Page number starts at 1

            # Calculate the text width to center or adjust the position manually
            text_width = fitz.get_text_length(text, fontsize=font_size)

            # Define position: bottom-center, bottom-right, etc.
            if position == 'bottom_center':
                x = (rect.width - text_width) / 2
                y = rect.height - 30
            elif position == 'bottom_left':
                x = 30
                y = rect.height - 30
            elif position == 'bottom_right':
                x = rect.width - text_width - 30
                y = rect.height - 30
            elif position == 'top_center':
                x = (rect.width - text_width) / 2
                y = 30
            elif position == 'top_left':
                x = 30
                y = 30
            elif position == 'top_right':
                x = rect.width - text_width - 30
                y = 30
            else:
                return jsonify({"error": "Invalid position selected"}), 400

            # Insert the page number as text
            page.insert_text((x, y), text, fontsize=font_size)

            output_pdf.insert_pdf(pdf, from_page=page_number, to_page=page_number)

        output_path = os.path.join(output_dir, f'page_numbered_{file.filename}')
        output_pdf.save(output_path)
        output_pdf.close()
        pdf.close()
        logging.debug(f"PDF with page numbers saved: {output_path}")

    except Exception as e:
        logging.error(f"Error adding page numbers: {e}")
        return jsonify({"error": "Failed to add page numbers to PDF"}), 500

    return send_file(output_path, as_attachment=True)

