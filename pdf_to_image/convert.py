from flask import Blueprint, jsonify, render_template, request, send_file
import os
import subprocess
import tempfile
import zipfile
import logging
import shutil
from PIL import Image
import fitz

logging.basicConfig(level=logging.DEBUG)

convert_bp = Blueprint('convert', __name__)

STATIC_DIR = os.path.join(os.getcwd(), 'pdf_to_image', 'static')

# Ensure the static directory exists
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

def convert_pdf_to_images_ghostscript(pdf_path, output_dir, dpi=300, format_type='jpeg', pages='all'):
    """Convert PDF to images using Ghostscript"""
    try:
        # Determine device based on format
        device_map = {
            'jpeg': 'jpeg',
            'jpg': 'jpeg',
            'png': 'png16m',
            'tiff': 'tiff24nc'
        }
        device = device_map.get(format_type.lower(), 'jpeg')

        # Build Ghostscript command
        gs_command = [
            'gs',
            '-dNOPAUSE',
            '-dBATCH',
            '-dSAFER',
            '-dQUIET',
            f'-sDEVICE={device}',
            f'-r{dpi}',
            '-dTextAlphaBits=4',
            '-dGraphicsAlphaBits=4',
            f'-sOutputFile={os.path.join(output_dir, "page_%03d." + format_type.lower())}',
            pdf_path
        ]

        # Add page range if specified
        if pages != 'all':
            if '-' in pages:
                start, end = pages.split('-')
                gs_command.insert(-1, f'-dFirstPage={start}')
                gs_command.insert(-1, f'-dLastPage={end}')
            else:
                gs_command.insert(-1, f'-dFirstPage={pages}')
                gs_command.insert(-1, f'-dLastPage={pages}')

        logging.debug(f"Running Ghostscript command: {' '.join(gs_command)}")
        result = subprocess.run(gs_command, capture_output=True, text=True)

        if result.returncode != 0:
            logging.error(f"Ghostscript error: {result.stderr}")
            raise Exception(f"Ghostscript conversion failed: {result.stderr}")

        # Get list of generated files
        output_files = []
        for file in os.listdir(output_dir):
            if file.startswith('page_') and file.endswith(f'.{format_type.lower()}'):
                output_files.append(os.path.join(output_dir, file))

        output_files.sort()
        return output_files

    except Exception as e:
        logging.error(f"Error in Ghostscript conversion: {e}")
        raise

@convert_bp.route('/pdf_to_jpg', methods=['POST'])
def convert_pdf_to_jpg():
    """Handle PDF to JPG conversion requests"""
    try:
        file = request.files['file']

        # Get options from form
        dpi = int(request.form.get('dpi', 300))
        format_type = request.form.get('format', 'jpeg').lower()
        pages = request.form.get('pages', 'all')
        quality = request.form.get('quality', 'high')

        logging.debug(f"Converting PDF to {format_type} with DPI: {dpi}, Pages: {pages}")

        with tempfile.TemporaryDirectory() as temp_dir:
            # Save uploaded PDF
            pdf_path = os.path.join(temp_dir, file.filename)
            file.save(pdf_path)

            # Create output directory
            output_dir = os.path.join(temp_dir, 'images')
            os.makedirs(output_dir, exist_ok=True)

            # Convert PDF to images
            image_files = convert_pdf_to_images_ghostscript(
                pdf_path, output_dir, dpi, format_type, pages
            )

            if not image_files:
                return jsonify({"error": "No images were generated"}), 500

            # If single image, return it directly
            if len(image_files) == 1:
                return send_file(image_files[0], as_attachment=True,
                               download_name=f'{os.path.splitext(file.filename)[0]}.{format_type}')

            # Multiple images - create ZIP
            zip_path = os.path.join(temp_dir, f'{os.path.splitext(file.filename)[0]}_images.zip')
            with zipfile.ZipFile(zip_path, 'w') as zip_file:
                for i, img_file in enumerate(image_files, 1):
                    zip_file.write(img_file, f'page_{i:03d}.{format_type}')

            return send_file(zip_path, as_attachment=True,
                           download_name=f'{os.path.splitext(file.filename)[0]}_images.zip')

    except Exception as e:
        logging.error(f"Error in PDF to JPG conversion: {e}")
        return jsonify({"error": str(e)}), 500

@convert_bp.route('/get_total_pages', methods=['POST'])
def get_total_pages():
    """Get total pages in PDF for preview"""
    try:
        file = request.files['file']
        pdf = fitz.open(stream=file.read(), filetype='pdf')
        total_pages = pdf.page_count
        pdf.close()
        return jsonify({"total_pages": total_pages})
    except Exception as e:
        logging.error(f"Error getting page count: {e}")
        return jsonify({"total_pages": 1})