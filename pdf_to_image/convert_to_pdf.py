from flask import Blueprint, request, send_file, jsonify
import fitz  # PyMuPDF
import os
import zipfile
from PIL import Image
import io
import tempfile
import logging
import uuid
from datetime import datetime

convert_to_pdf_bp = Blueprint('convert_to_pdf', __name__)

STATIC_DIR = os.path.join(os.getcwd(), 'pdf_to_image', 'static')

# Ensure the static directory exists
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Supported image formats
SUPPORTED_IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.gif'}

# Page size configurations (width, height in points)
PAGE_SIZES = {
    'A4': (595, 842),
    'Letter': (612, 792),
    'Legal': (612, 1008),
    'A3': (842, 1191),
    'A5': (420, 595)
}

def validate_file(file, allowed_extensions):
    """Validate uploaded file"""
    if not file or file.filename == '':
        return False, "No file selected"

    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        return False, f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"

    # Check file size (max 50MB)
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    if file_size > 50 * 1024 * 1024:  # 50MB
        return False, "File too large. Maximum size is 50MB"

    return True, "Valid file"

def convert_images_to_pdf(images, output_path, page_size='A4', quality=95):
    """Convert multiple images to PDF with specified page size and quality"""
    try:
        pdf_doc = fitz.open()
        page_width, page_height = PAGE_SIZES.get(page_size, PAGE_SIZES['A4'])

        for image_data in images:
            if hasattr(image_data, 'seek'):
                image_data.seek(0)
                img = Image.open(image_data)
            else:
                img = Image.open(io.BytesIO(image_data))

            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # Calculate scaling to fit page while maintaining aspect ratio
            img_width, img_height = img.size
            scale_x = page_width / img_width
            scale_y = page_height / img_height
            scale = min(scale_x, scale_y)

            new_width = int(img_width * scale)
            new_height = int(img_height * scale)

            # Resize image
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Save image to bytes
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG', quality=quality, optimize=True)
            img_byte_arr.seek(0)

            # Create PDF page
            page = pdf_doc.new_page(width=page_width, height=page_height)

            # Center image on page
            x_offset = (page_width - new_width) / 2
            y_offset = (page_height - new_height) / 2

            rect = fitz.Rect(x_offset, y_offset, x_offset + new_width, y_offset + new_height)
            page.insert_image(rect, stream=img_byte_arr.getvalue())

        pdf_doc.save(output_path)
        pdf_doc.close()
        return True, "Conversion successful"

    except Exception as e:
        logging.error(f"Error converting images to PDF: {str(e)}")
        return False, f"Conversion failed: {str(e)}"

@convert_to_pdf_bp.route('/api/jpg_to_pdf', methods=['POST'])
def jpg_to_pdf():
    """Convert JPG/PNG images to PDF"""
    try:
        # Validate file
        file = request.files.get('file')
        is_valid, message = validate_file(file, SUPPORTED_IMAGE_FORMATS)
        if not is_valid:
            return jsonify({"error": message}), 400

        # Get options
        page_size = request.form.get('page_size', 'A4')
        quality = int(request.form.get('quality', 95))

        # Generate unique filename
        unique_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"converted_images_{timestamp}_{unique_id}.pdf"
        output_path = os.path.join(STATIC_DIR, output_filename)

        # Convert single image
        success, message = convert_images_to_pdf([file], output_path, page_size, quality)

        if not success:
            return jsonify({"error": message}), 500

        return send_file(output_path, as_attachment=True, download_name=output_filename)

    except Exception as e:
        logging.error(f"Error in jpg_to_pdf: {str(e)}")
        return jsonify({"error": f"Conversion failed: {str(e)}"}), 500

@convert_to_pdf_bp.route('/api/zip_to_pdf', methods=['POST'])
def zip_to_pdf():
    """Convert ZIP archive of images to PDF"""
    try:
        # Validate file
        file = request.files.get('file')
        is_valid, message = validate_file(file, {'.zip'})
        if not is_valid:
            return jsonify({"error": message}), 400

        # Get options
        page_size = request.form.get('page_size', 'A4')
        quality = int(request.form.get('quality', 95))

        # Generate unique filename
        unique_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"converted_zip_{timestamp}_{unique_id}.pdf"
        output_path = os.path.join(STATIC_DIR, output_filename)

        # Extract and process images from ZIP
        with tempfile.TemporaryDirectory() as temp_dir:
            with zipfile.ZipFile(file, 'r') as zip_ref:
                # Extract all files
                zip_ref.extractall(temp_dir)

                # Find image files
                image_files = []
                for root, dirs, files in os.walk(temp_dir):
                    for filename in sorted(files):  # Sort for consistent order
                        file_ext = os.path.splitext(filename)[1].lower()
                        if file_ext in SUPPORTED_IMAGE_FORMATS:
                            image_path = os.path.join(root, filename)
                            with open(image_path, 'rb') as img_file:
                                image_files.append(img_file.read())

                if not image_files:
                    return jsonify({"error": "No supported image files found in ZIP archive"}), 400

                # Convert images to PDF
                success, message = convert_images_to_pdf(image_files, output_path, page_size, quality)

                if not success:
                    return jsonify({"error": message}), 500

        return send_file(output_path, as_attachment=True, download_name=output_filename)

    except Exception as e:
        logging.error(f"Error in zip_to_pdf: {str(e)}")
        return jsonify({"error": f"Conversion failed: {str(e)}"}), 500
