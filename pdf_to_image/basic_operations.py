"""
Basic PDF operations for core functionality
Handles PDF to image conversion, merging, splitting, and protection
"""

from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import uuid
import tempfile
import logging
import subprocess
from datetime import datetime
import PyPDF2
import fitz  # PyMuPDF
from PIL import Image
import zipfile

# Create blueprint
basic_operations_bp = Blueprint('basic_operations', __name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# File size limit (50MB)
MAX_FILE_SIZE = 50 * 1024 * 1024

# Static directory for file storage
STATIC_DIR = os.path.join(os.path.dirname(__file__), 'static')
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

def validate_pdf_file(file):
    """Validate uploaded PDF file"""
    if not file or not file.filename:
        return False, "No file selected"

    if not file.filename.lower().endswith('.pdf'):
        return False, "Only PDF files are allowed"

    # Check file size (approximate)
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # Reset file pointer

    if file_size > MAX_FILE_SIZE:
        return False, f"File size exceeds {MAX_FILE_SIZE // (1024*1024)}MB limit"

    return True, "Valid"

@basic_operations_bp.route('/pdf_to_jpg', methods=['POST'])
def pdf_to_jpg():
    """Convert PDF to JPG/PNG/TIFF images"""
    try:
        # Get file from request
        if 'file' not in request.files:
            return jsonify({"error": "No file part in request"}), 400

        file = request.files['file']

        # Validate file
        is_valid, message = validate_pdf_file(file)
        if not is_valid:
            return jsonify({"error": message}), 400

        # Get form parameters
        output_format = request.form.get('output_format', 'jpg').lower()
        quality = request.form.get('quality', 'high')
        resolution = int(request.form.get('resolution', '300'))

        # Validate parameters
        if output_format not in ['jpg', 'png', 'tiff']:
            output_format = 'jpg'
        
        if quality not in ['high', 'medium', 'low']:
            quality = 'high'

        # Create secure filenames
        original_filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())[:8]
        input_filename = f"{unique_id}_{original_filename}"
        
        input_path = os.path.join(STATIC_DIR, input_filename)

        # Save uploaded file
        file.save(input_path)
        logging.debug(f"File saved to: {input_path}")

        # Convert PDF to images using PyMuPDF
        doc = fitz.open(input_path)
        image_files = []
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            
            # Set quality based on user selection
            if quality == 'high':
                mat = fitz.Matrix(resolution/72, resolution/72)
            elif quality == 'medium':
                mat = fitz.Matrix((resolution*0.8)/72, (resolution*0.8)/72)
            else:  # low
                mat = fitz.Matrix((resolution*0.6)/72, (resolution*0.6)/72)
            
            pix = page.get_pixmap(matrix=mat)
            
            # Create output filename
            output_filename = f"{unique_id}_page_{page_num + 1}.{output_format}"
            output_path = os.path.join(STATIC_DIR, output_filename)
            
            if output_format == 'jpg':
                pix.save(output_path, output="jpeg")
            elif output_format == 'png':
                pix.save(output_path, output="png")
            elif output_format == 'tiff':
                pix.save(output_path, output="tiff")
            
            image_files.append(output_path)
        
        doc.close()

        # If multiple pages, create a ZIP file
        if len(image_files) > 1:
            zip_filename = f"converted_{unique_id}.zip"
            zip_path = os.path.join(STATIC_DIR, zip_filename)
            
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for img_path in image_files:
                    zipf.write(img_path, os.path.basename(img_path))
            
            # Clean up individual image files
            for img_path in image_files:
                try:
                    os.remove(img_path)
                except:
                    pass
            
            # Clean up input file
            try:
                os.remove(input_path)
            except:
                pass
            
            return send_file(zip_path, as_attachment=True, download_name=zip_filename)
        else:
            # Single page, return the image directly
            output_path = image_files[0]
            download_name = f"converted_{original_filename.rsplit('.', 1)[0]}.{output_format}"
            
            # Clean up input file
            try:
                os.remove(input_path)
            except:
                pass
            
            return send_file(output_path, as_attachment=True, download_name=download_name)

    except Exception as e:
        logging.error(f"Error in PDF to JPG conversion: {str(e)}")
        return jsonify({"error": f"Conversion failed: {str(e)}"}), 500

@basic_operations_bp.route('/merge', methods=['POST'])
def merge_pdfs():
    """Merge multiple PDF files"""
    try:
        # Get files from request
        files = request.files.getlist('files')
        
        if len(files) < 2:
            return jsonify({"error": "At least 2 PDF files are required for merging"}), 400

        # Validate all files
        temp_files = []
        for file in files:
            is_valid, message = validate_pdf_file(file)
            if not is_valid:
                return jsonify({"error": f"Invalid file {file.filename}: {message}"}), 400
            
            # Save temporary file
            unique_id = str(uuid.uuid4())[:8]
            temp_filename = f"temp_{unique_id}_{secure_filename(file.filename)}"
            temp_path = os.path.join(STATIC_DIR, temp_filename)
            file.save(temp_path)
            temp_files.append(temp_path)

        # Get form parameters
        output_filename = request.form.get('output_filename', 'merged_document.pdf')
        if not output_filename.endswith('.pdf'):
            output_filename += '.pdf'
        
        # Create output file
        unique_id = str(uuid.uuid4())[:8]
        output_path = os.path.join(STATIC_DIR, f"{unique_id}_{secure_filename(output_filename)}")

        # Merge PDFs using PyPDF2
        merger = PyPDF2.PdfMerger()
        
        for temp_file in temp_files:
            merger.append(temp_file)
        
        merger.write(output_path)
        merger.close()

        # Clean up temporary files
        for temp_file in temp_files:
            try:
                os.remove(temp_file)
            except:
                pass

        return send_file(output_path, as_attachment=True, download_name=output_filename)

    except Exception as e:
        logging.error(f"Error in PDF merge: {str(e)}")
        return jsonify({"error": f"Merge failed: {str(e)}"}), 500

@basic_operations_bp.route('/split', methods=['POST'])
def split_pdf():
    """Split PDF into multiple files"""
    try:
        # Get file from request
        if 'file' not in request.files:
            return jsonify({"error": "No file part in request"}), 400

        file = request.files['file']

        # Validate file
        is_valid, message = validate_pdf_file(file)
        if not is_valid:
            return jsonify({"error": message}), 400

        # Get form parameters
        split_method = request.form.get('split_method', 'pages')
        page_ranges = request.form.get('page_ranges', '')
        
        # Create secure filenames
        original_filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())[:8]
        input_filename = f"{unique_id}_{original_filename}"
        
        input_path = os.path.join(STATIC_DIR, input_filename)

        # Save uploaded file
        file.save(input_path)

        # Read PDF
        with open(input_path, 'rb') as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            total_pages = len(reader.pages)

            if split_method == 'pages' and page_ranges:
                # Parse page ranges (e.g., "1-3, 5, 7-10")
                ranges = []
                for part in page_ranges.split(','):
                    part = part.strip()
                    if '-' in part:
                        start, end = map(int, part.split('-'))
                        ranges.extend(range(start-1, end))  # Convert to 0-based
                    else:
                        ranges.append(int(part)-1)  # Convert to 0-based
                
                # Create single output file with selected pages
                writer = PyPDF2.PdfWriter()
                for page_num in ranges:
                    if 0 <= page_num < total_pages:
                        writer.add_page(reader.pages[page_num])
                
                output_filename = f"split_{unique_id}_{original_filename}"
                output_path = os.path.join(STATIC_DIR, output_filename)
                
                with open(output_path, 'wb') as output_file:
                    writer.write(output_file)
                
                # Clean up input file
                try:
                    os.remove(input_path)
                except:
                    pass
                
                return send_file(output_path, as_attachment=True, download_name=f"split_{original_filename}")
            
            else:
                # Split into individual pages
                output_files = []
                base_name = original_filename.rsplit('.', 1)[0]
                
                for page_num in range(total_pages):
                    writer = PyPDF2.PdfWriter()
                    writer.add_page(reader.pages[page_num])
                    
                    output_filename = f"{unique_id}_page_{page_num + 1}_{base_name}.pdf"
                    output_path = os.path.join(STATIC_DIR, output_filename)
                    
                    with open(output_path, 'wb') as output_file:
                        writer.write(output_file)
                    
                    output_files.append(output_path)
                
                # Create ZIP file
                zip_filename = f"split_{unique_id}_{base_name}.zip"
                zip_path = os.path.join(STATIC_DIR, zip_filename)
                
                with zipfile.ZipFile(zip_path, 'w') as zipf:
                    for output_file in output_files:
                        zipf.write(output_file, os.path.basename(output_file))
                
                # Clean up individual files
                for output_file in output_files:
                    try:
                        os.remove(output_file)
                    except:
                        pass
                
                # Clean up input file
                try:
                    os.remove(input_path)
                except:
                    pass
                
                return send_file(zip_path, as_attachment=True, download_name=zip_filename)

    except Exception as e:
        logging.error(f"Error in PDF split: {str(e)}")
        return jsonify({"error": f"Split failed: {str(e)}"}), 500

@basic_operations_bp.route('/protect', methods=['POST'])
def protect_pdf():
    """Add password protection to PDF"""
    try:
        # Get file from request
        if 'file' not in request.files:
            return jsonify({"error": "No file part in request"}), 400

        file = request.files['file']

        # Validate file
        is_valid, message = validate_pdf_file(file)
        if not is_valid:
            return jsonify({"error": message}), 400

        # Get form parameters
        user_password = request.form.get('user_password', '')
        owner_password = request.form.get('owner_password', '')

        if not user_password:
            return jsonify({"error": "User password is required"}), 400

        # Create secure filenames
        original_filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())[:8]
        input_filename = f"{unique_id}_{original_filename}"
        output_filename = f"protected_{unique_id}_{original_filename}"

        input_path = os.path.join(STATIC_DIR, input_filename)
        output_path = os.path.join(STATIC_DIR, output_filename)

        # Save uploaded file
        file.save(input_path)

        # Add password protection using PyPDF2
        with open(input_path, 'rb') as input_file:
            reader = PyPDF2.PdfReader(input_file)
            writer = PyPDF2.PdfWriter()

            # Copy all pages
            for page in reader.pages:
                writer.add_page(page)

            # Add password protection
            writer.encrypt(
                user_password=user_password,
                owner_password=owner_password if owner_password else user_password,
                use_128bit=True
            )

            # Write protected PDF
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)

        # Clean up input file
        try:
            os.remove(input_path)
        except:
            pass

        return send_file(output_path, as_attachment=True, download_name=f"protected_{original_filename}")

    except Exception as e:
        logging.error(f"Error in PDF protection: {str(e)}")
        return jsonify({"error": f"Protection failed: {str(e)}"}), 500

@basic_operations_bp.route('/pdf_to_panoramic', methods=['POST'])
def pdf_to_panoramic():
    """Convert PDF pages to panoramic image using Ghostscript"""
    try:
        # Get file from request
        if 'file' not in request.files:
            return jsonify({"error": "No file part in request"}), 400

        file = request.files['file']

        # Validate file
        is_valid, message = validate_pdf_file(file)
        if not is_valid:
            return jsonify({"error": message}), 400

        # Get form parameters
        stitch_direction = request.form.get('stitch_direction', 'horizontal')
        pages = request.form.get('pages', 'all')
        page_range = request.form.get('page_range', '')
        output_format = request.form.get('output_format', 'jpg')
        quality = request.form.get('quality', 'high')
        spacing = request.form.get('spacing', 'none')

        # Validate parameters
        if stitch_direction not in ['horizontal', 'vertical']:
            stitch_direction = 'horizontal'

        if output_format not in ['jpg', 'png', 'webp']:
            output_format = 'jpg'

        if quality not in ['high', 'medium', 'low']:
            quality = 'high'

        # Set DPI based on quality
        dpi_map = {'high': 300, 'medium': 150, 'low': 72}
        dpi = dpi_map[quality]

        # Create secure filenames
        original_filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())[:8]
        input_filename = f"{unique_id}_{original_filename}"

        input_path = os.path.join(STATIC_DIR, input_filename)

        # Save uploaded file
        file.save(input_path)
        logging.debug(f"File saved to: {input_path}")

        # Get total pages using PyPDF2
        with open(input_path, 'rb') as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            total_pages = len(reader.pages)

        # Determine which pages to process
        page_list = []
        if pages == 'all':
            page_list = list(range(1, total_pages + 1))
        elif pages == 'odd':
            page_list = list(range(1, total_pages + 1, 2))
        elif pages == 'even':
            page_list = list(range(2, total_pages + 1, 2))
        elif pages == 'range' and page_range:
            # Parse page range (e.g., "1-3,5,7-10")
            for part in page_range.split(','):
                part = part.strip()
                if '-' in part:
                    start, end = map(int, part.split('-'))
                    page_list.extend(range(start, min(end + 1, total_pages + 1)))
                else:
                    page_num = int(part)
                    if 1 <= page_num <= total_pages:
                        page_list.append(page_num)

        if not page_list:
            page_list = [1]  # Default to first page

        # Convert pages to images using Ghostscript
        temp_images = []
        for page_num in page_list:
            temp_image = os.path.join(STATIC_DIR, f"{unique_id}_page_{page_num}.png")

            # Ghostscript command to convert specific page to PNG
            gs_cmd = [
                'gs',
                '-dNOPAUSE',
                '-dBATCH',
                '-dSAFER',
                '-sDEVICE=png16m',
                f'-r{dpi}',
                f'-dFirstPage={page_num}',
                f'-dLastPage={page_num}',
                f'-sOutputFile={temp_image}',
                input_path
            ]

            result = subprocess.run(gs_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logging.error(f"Ghostscript error: {result.stderr}")
                # Cleanup and return error
                try:
                    os.remove(input_path)
                except:
                    pass
                return jsonify({"error": "Failed to convert PDF pages to images"}), 500

            temp_images.append(temp_image)

        # Load images and create panoramic
        from PIL import Image
        images = []
        for img_path in temp_images:
            if os.path.exists(img_path):
                images.append(Image.open(img_path))

        if not images:
            return jsonify({"error": "No images were generated"}), 500

        # Calculate spacing
        spacing_pixels = 0
        if spacing == 'small':
            spacing_pixels = 10
        elif spacing == 'medium':
            spacing_pixels = 20
        elif spacing == 'large':
            spacing_pixels = 40

        # Create panoramic image
        if stitch_direction == 'horizontal':
            # Horizontal stitching (side by side)
            total_width = sum(img.width for img in images) + spacing_pixels * (len(images) - 1)
            max_height = max(img.height for img in images)
            panoramic = Image.new('RGB', (total_width, max_height), 'white')

            x_offset = 0
            for img in images:
                # Center vertically
                y_offset = (max_height - img.height) // 2
                panoramic.paste(img, (x_offset, y_offset))
                x_offset += img.width + spacing_pixels
        else:
            # Vertical stitching (top to bottom)
            max_width = max(img.width for img in images)
            total_height = sum(img.height for img in images) + spacing_pixels * (len(images) - 1)
            panoramic = Image.new('RGB', (max_width, total_height), 'white')

            y_offset = 0
            for img in images:
                # Center horizontally
                x_offset = (max_width - img.width) // 2
                panoramic.paste(img, (x_offset, y_offset))
                y_offset += img.height + spacing_pixels

        # Save panoramic image
        output_filename = f"panoramic_{unique_id}_{original_filename.rsplit('.', 1)[0]}.{output_format}"
        output_path = os.path.join(STATIC_DIR, output_filename)

        if output_format == 'jpg':
            panoramic.save(output_path, 'JPEG', quality=95)
        elif output_format == 'png':
            panoramic.save(output_path, 'PNG')
        elif output_format == 'webp':
            panoramic.save(output_path, 'WebP', quality=95)

        # Clean up temporary files
        try:
            os.remove(input_path)
            for img_path in temp_images:
                if os.path.exists(img_path):
                    os.remove(img_path)
        except:
            pass

        return send_file(output_path, as_attachment=True, download_name=output_filename)

    except Exception as e:
        logging.error(f"Error in PDF to panoramic conversion: {str(e)}")
        return jsonify({"error": f"Panoramic conversion failed: {str(e)}"}), 500
