from flask import Blueprint, request, send_file
import fitz  # PyMuPDF
import os
from pptx import Presentation
from pptx.util import Inches, Pt
from PIL import Image

pdf_to_powerpoint_bp = Blueprint('pdf_to_powerpoint', __name__)

STATIC_DIR = os.path.join(os.getcwd(), 'pdf_to_image', 'static')

# Ensure the static directory exists
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

@pdf_to_powerpoint_bp.route('/pdf_to_powerpoint', methods=['POST'])
def pdf_to_powerpoint():
    file = request.files['file']
    file_path = os.path.join(STATIC_DIR, file.filename)
    file.save(file_path)

    doc = fitz.open(file_path)
    presentation = Presentation()

    # Set slide dimensions to match PDF page dimensions
    first_page = doc.load_page(0)
    page_rect = first_page.rect
    pdf_width = Inches(page_rect.width / 72)  # Convert points to inches
    pdf_height = Inches(page_rect.height / 72)  # Convert points to inches
    presentation.slide_width = pdf_width
    presentation.slide_height = pdf_height

    # Set desired resolution (e.g., 300 DPI)
    zoom = 3.0  # 3.0 corresponds to 300 DPI

    for page_number in range(len(doc)):
        page = doc.load_page(page_number)
        mat = fitz.Matrix(zoom, zoom)  # Use the matrix to scale the image
        pix = page.get_pixmap(matrix=mat)
        image_path = os.path.join(STATIC_DIR, f'{file.filename}_page_{page_number + 1}.jpg')
        pix.save(image_path)
        
        # Add a slide to the presentation
        slide_layout = presentation.slide_layouts[5]  # Using a blank slide layout
        slide = presentation.slides.add_slide(slide_layout)
        
        # Add image to the slide
        slide.shapes.add_picture(image_path, 0, 0, width=pdf_width, height=pdf_height)

    pptx_path = os.path.join(STATIC_DIR, f'{os.path.splitext(file.filename)[0]}.pptx')
    presentation.save(pptx_path)

    return send_file(pptx_path, as_attachment=True)
