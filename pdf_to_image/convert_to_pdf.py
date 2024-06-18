from flask import Blueprint, request, send_file
import fitz  # PyMuPDF
import os
import zipfile
from PIL import Image
import io

convert_to_pdf_bp = Blueprint('convert_to_pdf', __name__)

STATIC_DIR = os.path.join(os.getcwd(), 'pdf_to_image', 'static')

# Ensure the static directory exists
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

def convert_images_to_pdf(images, output_path):
    pdf_doc = fitz.open()
    for image in images:
        image.seek(0)
        img = Image.open(image)
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        img_pix = fitz.Pixmap(img_byte_arr)
        img_doc = fitz.open()
        rect = fitz.Rect(0, 0, img_pix.width, img_pix.height)
        page = img_doc.new_page(width=rect.width, height=rect.height)
        page.insert_image(rect, pixmap=img_pix)
        pdfbytes = img_doc.convert_to_pdf()
        img_doc.close()

        img_pdf = fitz.open("pdf", pdfbytes)
        pdf_doc.insert_pdf(img_pdf)
    pdf_doc.save(output_path)
    pdf_doc.close()

@convert_to_pdf_bp.route('/convert_to_pdf', methods=['POST'])
def convert_to_pdf():
    file = request.files['file']
    file_extension = os.path.splitext(file.filename)[1].lower()

    if file_extension not in ['.jpg', '.jpeg', '.png', '.html', '.zip']:
        return {"error": "Unsupported file type"}, 400

    output_path = os.path.join(STATIC_DIR, f'{os.path.splitext(file.filename)[0]}.pdf')

    try:
        if file_extension in ['.jpg', '.jpeg', '.png']:
            img_doc = fitz.open()
            img = fitz.open(stream=file.read(), filetype=file_extension[1:])
            pdfbytes = img.convert_to_pdf()
            img.close()
            img_doc.insert_pdf(fitz.open("pdf", pdfbytes))
            img_doc.save(output_path)
            img_doc.close()
        elif file_extension == '.html':
            doc = fitz.open(stream=file.read(), filetype='html')
            doc.save(output_path)
            doc.close()
        elif file_extension == '.zip':
            with zipfile.ZipFile(file, 'r') as zip_ref:
                image_files = [zip_ref.open(name) for name in zip_ref.namelist() if name.lower().endswith(('.jpg', '.jpeg', '.png'))]
                convert_images_to_pdf(image_files, output_path)
    except Exception as e:
        return {"error": str(e)}, 500

    return send_file(output_path, as_attachment=True)
