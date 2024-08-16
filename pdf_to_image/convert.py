from flask import Blueprint, request, send_file, jsonify, render_template
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
    try:
        file = request.files['file']
        file_path = os.path.join(STATIC_DIR, file.filename)
        file.save(file_path)

        doc = fitz.open(file_path)
        image_paths = []

        # Get selected pages from the form data
        selected_pages = request.form.getlist('pages')
        selected_pages = [int(page) - 1 for page in selected_pages]  # Convert to zero indexed

        # Set desired resolution based on user input
        dpi = int(request.form.get('dpi', 300))
        zoom = dpi / 72.0  # Convert DPI to zoom level

        for page_number in selected_pages:
            page = doc.load_page(page_number)
            mat = fitz.Matrix(zoom, zoom)  # Use the matrix to scale the image
            pix = page.get_pixmap(matrix=mat)
            output_format = request.form.get('format', 'jpg').lower()
            image_path = os.path.join(STATIC_DIR, f'{file.filename}_page_{page_number + 1}.{output_format}')
            pix.save(image_path)
            image_paths.append(image_path)

        # Create a ZIP file containing all the images
        zip_path = os.path.join(STATIC_DIR, f'{file.filename}.zip')
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for image_path in image_paths:
                zipf.write(image_path, os.path.basename(image_path))

        # Send the ZIP file
        return send_file(zip_path, as_attachment=True)
    
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
        file_path = os.path.join(STATIC_DIR, file.filename)
        file.save(file_path)

        doc = fitz.open(file_path)
        total_pages = len(doc)

        return jsonify({"total_pages": total_pages})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
