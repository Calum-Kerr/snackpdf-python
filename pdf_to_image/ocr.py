from flask import Blueprint, request, send_file, jsonify
import fitz  # PyMuPDF
import os
import logging
import shutil
import tempfile

ocr_bp = Blueprint('ocr', __name__)

STATIC_DIR = os.path.join(os.getcwd(), 'pdf_to_image', 'static')

# Ensure the static directory exists
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

@ocr_bp.route('/ocr', methods=['POST'])
def ocr_pdf():
    file = request.files['file']
    output_dir = os.path.join(STATIC_DIR, 'ocr')

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    try:
        logging.debug(f"Processing file: {file.filename}")
        pdf = fitz.open(stream=file.read(), filetype='pdf')

        # Use a temporary file to collect all text
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as text_file:
            # Loop over each page in the PDF and extract text
            for page_number in range(pdf.page_count):
                page = pdf.load_page(page_number)

                # Directly extract text from the page
                extracted_text = page.get_text("text")

                # Write the extracted text to the text file
                text_file.write(f"\n--- Page {page_number + 1} ---\n".encode('utf-8'))
                text_file.write(extracted_text.encode('utf-8'))

            text_file_path = text_file.name

        pdf.close()

        # Return the text file as a download
        return send_file(text_file_path, as_attachment=True, download_name=f'{os.path.splitext(file.filename)[0]}.txt')

    except Exception as e:
        logging.error(f"Error performing text extraction: {e}")
        return jsonify({"error": "Failed to extract text from PDF"}), 500