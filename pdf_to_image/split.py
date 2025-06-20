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
    split_method = request.form.get('split_method', 'page_ranges')
    page_ranges = request.form.get('page_ranges', '')
    pages_per_split = int(request.form.get('pages_per_split', 1))
    max_size_mb = int(request.form.get('max_size_mb', 10))
    output_format = request.form.get('output_format', 'zip_archive')
    preserve_bookmarks = request.form.get('preserve_bookmarks', 'true') == 'true'

    output_dir = os.path.join(STATIC_DIR, 'split')

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    try:
        logging.debug(f"Processing file: {file.filename}")
        pdf = fitz.open(stream=file.read(), filetype='pdf')
        total_pages = pdf.page_count

        if split_method == 'page_ranges' and page_ranges:
            ranges = page_ranges.split(',')
            for i, range_str in enumerate(ranges):
                range_str = range_str.strip()
                if '-' in range_str:
                    start, end = map(int, range_str.split('-'))
                else:
                    start = end = int(range_str)

                output_path = os.path.join(output_dir, f'split_{i+1}_pages_{start}_to_{end}.pdf')
                split_pdf = fitz.open()
                split_pdf.insert_pdf(pdf, from_page=start-1, to_page=end-1)
                split_pdf.save(output_path)
                split_pdf.close()
                logging.debug(f"Created split PDF: {output_path}")

        elif split_method == 'every_n_pages':
            for i in range(0, total_pages, pages_per_split):
                start_page = i
                end_page = min(i + pages_per_split - 1, total_pages - 1)

                output_path = os.path.join(output_dir, f'split_{i//pages_per_split + 1}_pages_{start_page+1}_to_{end_page+1}.pdf')
                split_pdf = fitz.open()
                split_pdf.insert_pdf(pdf, from_page=start_page, to_page=end_page)
                split_pdf.save(output_path)
                split_pdf.close()
                logging.debug(f"Created split PDF: {output_path}")

        elif split_method == 'single_pages':
            for i in range(total_pages):
                output_path = os.path.join(output_dir, f'page_{i+1}.pdf')
                split_pdf = fitz.open()
                split_pdf.insert_pdf(pdf, from_page=i, to_page=i)
                split_pdf.save(output_path)
                split_pdf.close()
                logging.debug(f"Created split PDF: {output_path}")

        pdf.close()

        # Create output based on format preference
        if output_format == 'zip_archive':
            zip_path = os.path.join(STATIC_DIR, f'split_{file.filename}.zip')
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for foldername, subfolders, filenames in os.walk(output_dir):
                    for filename in filenames:
                        file_path = os.path.join(foldername, filename)
                        zipf.write(file_path, os.path.basename(file_path))
            logging.debug(f"Created zip file: {zip_path}")
            return send_file(zip_path, as_attachment=True)
        else:
            # Return first split file for separate_files option
            files = os.listdir(output_dir)
            if files:
                return send_file(os.path.join(output_dir, files[0]), as_attachment=True)
            else:
                return {"error": "No split files created"}, 500

    except Exception as e:
        logging.error(f"Error splitting PDF: {e}")
        return {"error": str(e)}, 500

