from flask import Blueprint, request, send_file, jsonify, render_template
import fitz  # PyMuPDF
from PIL import Image
import os
import logging

panoramic_bp = Blueprint('panoramic', __name__)

STATIC_DIR = os.path.join(os.getcwd(), 'pdf_to_image', 'static')

# Ensure the static directory exists
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

# Set up logging
logging.basicConfig(level=logging.DEBUG)

@panoramic_bp.route('/panoramic', methods=['POST'])
def panoramic():
    try:
        logging.debug("Processing file upload")
        if 'file' not in request.files:
            logging.error("No file part in the request.")
            return jsonify({"error": "No file part in the request."}), 400

        file = request.files['file']
        if file.filename == '':
            logging.error("No file selected.")
            return jsonify({"error": "No file selected."}), 400

        file_path = os.path.join(STATIC_DIR, file.filename)
        file.save(file_path)
        logging.debug(f"File saved to {file_path}")
    except Exception as e:
        logging.error(f"File upload failed: {str(e)}")
        return jsonify({"error": f"File upload failed: {str(e)}"}), 500

    try:
        logging.debug("Loading PDF")
        # Load the PDF
        doc = fitz.open(file_path)
        total_pages = len(doc)
        logging.debug(f"Total pages in PDF: {total_pages}")
    except Exception as e:
        logging.error(f"Failed to open PDF: {str(e)}")
        return jsonify({"error": f"Failed to open PDF: {str(e)}"}), 500

    images = []
    try:
        # Get DPI, orientation, and format from the form
        logging.debug("Fetching DPI, orientation, and format from the form")
        dpi = int(request.form.get('dpi', 300))
        zoom = dpi / 72.0  # Convert DPI to zoom level
        orientation = request.form.get('orientation', 'horizontal')
        output_format = request.form.get('format', 'jpg').lower()

        logging.debug(f"DPI: {dpi}, Orientation: {orientation}, Format: {output_format}")

        logging.debug("Processing all pages from the PDF")
        # Automatically process all pages in the PDF
        for page_number in range(total_pages):
            try:
                page = doc.load_page(page_number)
                mat = fitz.Matrix(zoom, zoom)  # Adjust the zoom based on the selected DPI
                pix = page.get_pixmap(matrix=mat)
                image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                images.append(image)
                logging.debug(f"Processed page {page_number + 1}")
            except Exception as e:
                logging.error(f"Failed to process page {page_number + 1}: {str(e)}")
                return jsonify({"error": f"Failed to process page {page_number + 1}: {str(e)}"}), 500
    except Exception as e:
        logging.error(f"Error during image conversion: {str(e)}")
        return jsonify({"error": f"Error during image conversion: {str(e)}"}), 500

    # Check if images list is empty before proceeding
    if not images:
        logging.error("No images were generated.")
        return jsonify({"error": "No images were generated."}), 500

    try:
        logging.debug("Stitching images into a panoramic image")
        # Calculate the dimensions of the panoramic image based on orientation
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
        logging.debug("Panoramic image stitched successfully")
    except Exception as e:
        logging.error(f"Error during image stitching: {str(e)}")
        return jsonify({"error": f"Error during image stitching: {str(e)}"}), 500

    try:
        logging.debug("Saving panoramic image")
        # Save the panoramic image in the selected format
        if output_format == 'jpg':
            panoramic_image = panoramic_image.convert('RGB')
            panoramic_image_path = os.path.join(STATIC_DIR, f'{file.filename}_panoramic.jpg')
            panoramic_image.save(panoramic_image_path, 'JPEG', quality=95)
        elif output_format == 'png':
            panoramic_image = panoramic_image.convert('RGBA')  # PNG supports RGBA
            panoramic_image_path = os.path.join(STATIC_DIR, f'{file.filename}_panoramic.png')
            panoramic_image.save(panoramic_image_path, 'PNG')
        else:
            panoramic_image_path = os.path.join(STATIC_DIR, f'{file.filename}_panoramic.{output_format}')
            panoramic_image.save(panoramic_image_path, output_format.upper())
        logging.debug(f"Panoramic image saved successfully as {output_format}")
    except Exception as e:
        logging.error(f"Error during image saving: {str(e)}")
        return jsonify({"error": f"Error during image saving: {str(e)}"}), 500

    try:
        logging.debug("Sending panoramic image to client")
        return send_file(panoramic_image_path, as_attachment=True, mimetype=f'image/{output_format}')
    except Exception as e:
        logging.error(f"Error during file sending: {str(e)}")
        return jsonify({"error": f"Error during file sending: {str(e)}"}), 500
