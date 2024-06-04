# pdf_to_image/1_convert.py
from flask import Blueprint, request, send_file
from pdf2image import convert_from_path
from PIL import Image
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

    images = convert_from_path(file_path)
    image_paths = []
    for i, image in enumerate(images):
        image_path = os.path.join(STATIC_DIR, f'{file.filename}_page_{i + 1}.jpg')
        image.save(image_path, 'JPEG')
        image_paths.append(image_path)

    # Create a ZIP file containing all the images
    zip_path = os.path.join(STATIC_DIR, f'{file.filename}.zip')
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for image_path in image_paths:
            zipf.write(image_path, os.path.basename(image_path))

    # Send the ZIP file
    return send_file(zip_path, as_attachment=True)
