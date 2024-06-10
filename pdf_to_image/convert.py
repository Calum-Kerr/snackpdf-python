from flask import Blueprint, request, send_file
import fitz  # PyMuPDF
import os
import zipfile

convert_bp = Blueprint('convert', __name__)

STATIC_DIR = os.path.join(os.getcwd(), 'pdf_to_image', 'static')

# Ensure the static directory exists
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

@convert_bp.route('/convert', methods=['POST'])
def convert():
    file = request.files['file']
    file_path = os.path.join(STATIC_DIR, file.filename)
    file.save(file_path)

    doc = fitz.open(file_path)
    image_paths = []

    for page_number in range(len(doc)):
        page = doc.load_page(page_number)
        pix = page.get_pixmap()
        image_path = os.path.join(STATIC_DIR, f'{file.filename}_page_{page_number + 1}.jpg')
        pix.save(image_path)
        image_paths.append(image_path)

    # Create a ZIP file containing all the images
    zip_path = os.path.join(STATIC_DIR, f'{file.filename}.zip')
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for image_path in image_paths:
            zipf.write(image_path, os.path.basename(image_path))

    # Send the ZIP file
    return send_file(zip_path, as_attachment=True)
