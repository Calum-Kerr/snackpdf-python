from flask import Blueprint, request, send_file, jsonify, render_template
import fitz  # PyMuPDF
import os
import zipfile
from io import BytesIO
import json
from PIL import Image
import tempfile

convert_bp = Blueprint('convert', __name__)

STATIC_DIR = os.path.join(os.getcwd(), 'pdf_to_image', 'static')

# Ensure the static directory exists
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

@convert_bp.route('/convert', methods=['POST'])
def convert():
    try:
        file = request.files['file']
        options = request.form.get('options')
        options = json.loads(options)  # Convert JSON string to Python dictionary

        # Create a temporary directory to store files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save the uploaded PDF file
            file_path = os.path.join(temp_dir, file.filename)
            file.save(file_path)

            # Open the PDF document
            doc = fitz.open(file_path)
            image_paths = []

            # Set desired resolution based on user input
            dpi = int(options.get('dpi', 300))
            zoom = dpi / 72.0  # Convert DPI to zoom level

            output_format = options.get('fileFormat', 'png').lower()
            color_mode = options.get('colorMode', 'rgb')
            page_size = options.get('pageSize', 'a4')
            maintain_aspect_ratio = options.get('maintainAspectRatio', True)
            extract_text = options.get('extractText', False)
            compress_output = options.get('compressOutput', False)

            # Set page size
            if page_size == 'custom':
                width = int(options.get('customWidth', 0))
                height = int(options.get('customHeight', 0))
            else:
                # Define standard page sizes (in pixels at 72 DPI)
                page_sizes = {
                    'a4': (595, 842),
                    'a5': (420, 595),
                    'letter': (612, 792),
                    'legal': (612, 1008)
                }
                width, height = page_sizes.get(page_size, page_sizes['a4'])

            # Scale dimensions according to DPI
            width = int(width * (dpi / 72))
            height = int(height * (dpi / 72))

            for page_number in range(len(doc)):
                page = doc.load_page(page_number)
                mat = fitz.Matrix(zoom, zoom)

                # Apply color mode
                if color_mode == 'rgb':
                    pix = page.get_pixmap(matrix=mat, alpha=False)
                elif color_mode == 'cmyk':
                    pix = page.get_pixmap(matrix=mat, alpha=False, colorspace=fitz.csRGB)  # PyMuPDF doesn't support CMYK output
                elif color_mode == 'grayscale':
                    pix = page.get_pixmap(matrix=mat, alpha=False, colorspace=fitz.csGRAY)
                elif color_mode == 'bw':
                    pix = page.get_pixmap(matrix=mat, alpha=False)
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    img = img.convert('1')  # Convert to black and white
                else:
                    pix = page.get_pixmap(matrix=mat, alpha=False)

                # Convert to PIL Image
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                # Resize image
                if maintain_aspect_ratio:
                    img.thumbnail((width, height), Image.LANCZOS)
                else:
                    img = img.resize((width, height), Image.LANCZOS)

                # Extract text if requested
                if extract_text:
                    text = page.get_text()
                    text_file_path = os.path.join(temp_dir, f'page_{page_number + 1}.txt')
                    with open(text_file_path, 'w', encoding='utf-8') as text_file:
                        text_file.write(text)
                    image_paths.append(text_file_path)

                # Save image
                image_path = os.path.join(temp_dir, f'page_{page_number + 1}.{output_format}')
                
                if output_format == 'jpg':
                    img = img.convert('RGB')
                    img.save(image_path, format='JPEG', quality=85 if compress_output else 95)
                elif output_format == 'png':
                    img.save(image_path, format='PNG', compress_level=6 if compress_output else 1)
                elif output_format == 'tiff':
                    img.save(image_path, format='TIFF', compression='tiff_deflate' if compress_output else None)
                elif output_format == 'webp':
                    img.save(image_path, format='WEBP', quality=85 if compress_output else 95)
                else:
                    raise ValueError(f"Unsupported output format: {output_format}")

                image_paths.append(image_path)

            # Create a ZIP file containing all the images and text files
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for path in image_paths:
                    zipf.write(path, os.path.basename(path))
            zip_buffer.seek(0)

            # Send the ZIP file
            return send_file(zip_buffer, as_attachment=True, download_name=f'{file.filename}_converted.zip', mimetype='application/zip')
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@convert_bp.route('/pdf_to_jpg')
def pdf_to_jpg():
    total_pages = 0
    uploaded_filename = ''
    return render_template('pdf_to_jpg.html', total_pages=total_pages, uploaded_filename=uploaded_filename)

@convert_bp.route('/get_total_pages', methods=['POST'])
def get_total_pages():
    try:
        file = request.files['file']
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            file.save(temp_file.name)
            doc = fitz.open(temp_file.name)
            total_pages = len(doc)
        os.unlink(temp_file.name)  # Delete the temporary file
        return jsonify({"total_pages": total_pages})
    except Exception as e:
        return jsonify({"error": str(e)}), 500