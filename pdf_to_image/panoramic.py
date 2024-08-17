from flask import Blueprint, request, send_file, jsonify, render_template
import fitz  # PyMuPDF
from PIL import Image
import os

panoramic_bp = Blueprint('panoramic', __name__)

STATIC_DIR = os.path.join(os.getcwd(), 'pdf_to_image', 'static')

# Ensure the static directory exists
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

@panoramic_bp.route('/panoramic', methods=['POST'])
def panoramic():
    file = request.files['file']
    file_path = os.path.join(STATIC_DIR, file.filename)
    file.save(file_path)

    # Load the PDF
    doc = fitz.open(file_path)
    images = []

    # Get selected pages
    selected_pages = request.form.getlist('pages')
    selected_pages = [int(page) - 1 for page in selected_pages]

    # Set desired resolution (DPI) from user input
    dpi = int(request.form.get('dpi', 300))
    zoom = dpi / 72.0  # Convert DPI to zoom level

    # Get the selected orientation
    orientation = request.form.get('orientation', 'horizontal')

    # Convert each selected page to an image
    for page_number in selected_pages:
        page = doc.load_page(page_number)
        mat = fitz.Matrix(zoom, zoom)  # Use the matrix to scale the image
        pix = page.get_pixmap(matrix=mat)
        image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(image)

    # Calculate the dimensions of the panoramic image
    if orientation == 'horizontal':
        total_width = sum(image.width for image in images)
        max_height = max(image.height for image in images)
        panoramic_image = Image.new('RGB', (total_width, max_height))

        x_offset = 0
        for image in images:
            panoramic_image.paste(image, (x_offset, 0))
            x_offset += image.width
    else:  # Vertical orientation
        max_width = max(image.width for image in images)
        total_height = sum(image.height for image in images)
        panoramic_image = Image.new('RGB', (max_width, total_height))

        y_offset = 0
        for image in images:
            panoramic_image.paste(image, (0, y_offset))
            y_offset += image.height

    # Save the panoramic image in the selected format
    output_format = request.form.get('format', 'jpg').lower()

    # Ensure the image is in RGB mode and handle JPEG specifically
    if output_format == 'jpg':
        panoramic_image = panoramic_image.convert('RGB')
        panoramic_image_path = os.path.join(STATIC_DIR, f'{file.filename}_panoramic.jpg')
        panoramic_image.save(panoramic_image_path, 'JPEG', quality=95)
    else:
        panoramic_image_path = os.path.join(STATIC_DIR, f'{file.filename}_panoramic.{output_format}')
        panoramic_image.save(panoramic_image_path, output_format.upper())

    return send_file(panoramic_image_path, as_attachment=True)

@panoramic_bp.route('/get_total_pages', methods=['POST'])
def get_total_pages():
    try:
        file = request.files['file']
        file_path = os.path.join(STATIC_DIR, file.filename)
        file.save(file_path)

        doc = fitz.open(file_path)
        total_pages = len(doc)

        return jsonify({"total_pages": total_pages})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@panoramic_bp.route('/pdf_to_panoramic')
def pdf_to_panoramic():
    total_pages = 0
    uploaded_filename = ''
    return render_template('pdf_to_panoramic.html', total_pages=total_pages, uploaded_filename=uploaded_filename)
