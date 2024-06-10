from flask import Blueprint, request, send_file
import fitz  # PyMuPDF
from PIL import Image
import os

panoramic_bp = Blueprint('panoramic', __name__)

STATIC_DIR = os.path.join(os.getcwd(), 'pdf_to_image', 'static')

@panoramic_bp.route('/panoramic', methods=['POST'])
def panoramic():
    file = request.files['file']
    file_path = os.path.join(STATIC_DIR, file.filename)
    file.save(file_path)

    doc = fitz.open(file_path)
    images = []

    for page_number in range(len(doc)):
        page = doc.load_page(page_number)
        pix = page.get_pixmap()
        image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(image)

    widths, heights = zip(*(i.size for i in images))
    total_width = sum(widths)
    max_height = max(heights)

    panoramic_image = Image.new('RGB', (total_width, max_height))
    x_offset = 0
    for image in images:
        panoramic_image.paste(image, (x_offset, 0))
        x_offset += image.width

    panoramic_image_path = os.path.join(STATIC_DIR, f'{file.filename}_panoramic.jpg')
    panoramic_image.save(panoramic_image_path, 'JPEG')

    return send_file(panoramic_image_path, as_attachment=True)
