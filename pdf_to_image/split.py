from flask import Blueprint, request, send_file
import fitz
import os
import zipfile
import logging
import shutil

logging.basicConfig(level=logging.DEBUG)

split_bp = Blueprint('split', __name__)

STATIC_DIR = os.path.join(os.getcwd(), 'pdf_to_image', 'static')

# Ensure the static directory exists
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

@split_bp.route('/split', methods=['POST'])
def split_pdf():
    file = request.files['file']
    page_ranges = request.form['page_ranges']
    output_dir = os.path.join(STATIC_DIR, 'split')

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    try:
        logging.debug(f"Processing file: {file.filename}")
        pdf = fitz.open(stream=file.read(), filetype='pdf')

        ranges = page_ranges.split(',')
        for range_str in ranges:
            start, end = map(int, range_str.split('-'))
            output_path = os.path.join(output_dir, f'split_pages_{start}_to_{end}.pdf')
            split_pdf = fitz.open()
            split_pdf.insert_pdf(pdf, from_page=start-1, to_page=end-1)
            split_pdf.save(output_path)
            split_pdf.close()
            logging.debug(f"Created split PDF: {output_path}")

        # Create a zip file for easier download
        zip_path = os.path.join(STATIC_DIR, 'split_files.zip')
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for foldername, subfolders, filenames in os.walk(output_dir):
                for filename in filenames:
                    file_path = os.path.join(foldername, filename)
                    zipf.write(file_path, os.path.basename(file_path))
        logging.debug(f"Created zip file: {zip_path}")
    except Exception as e:
        logging.error(f"Error splitting PDF: {e}")
        return {"error": str(e)}, 500

    return send_file(zip_path, as_attachment=True)

