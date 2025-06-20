from flask import Blueprint, request, send_file, jsonify
import os
import subprocess
import logging
import tempfile
import uuid
from werkzeug.utils import secure_filename

compress_bp = Blueprint('compress_bp', __name__)
STATIC_DIR = os.path.join(os.getcwd(), 'pdf_to_image', 'static')

# Ensure the static directory exists
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# File size limit (50MB)
MAX_FILE_SIZE = 50 * 1024 * 1024

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

def get_file_size(file_path):
    """Get file size in bytes"""
    try:
        return os.path.getsize(file_path)
    except OSError:
        return 0

def compress_pdf(input_path, output_path, quality, retain_metadata=True, resolution=None, fast_mode=False):
    """Compress PDF using Ghostscript with corrected quality settings"""
    # Corrected quality settings - higher quality = less compression
    quality_settings = {
        'high': '/prepress',    # Highest quality, least compression
        'medium': '/ebook',     # Medium quality, medium compression
        'low': '/screen',       # Lowest quality, most compression
        'lossless': '/prepress' # Lossless compression
    }
    gs_quality = quality_settings.get(quality, '/ebook')

    gs_command = [
        'gs', '-sDEVICE=pdfwrite',
        '-dCompatibilityLevel=1.4',
        f'-dPDFSETTINGS={gs_quality}',
        '-dNOPAUSE', '-dQUIET', '-dBATCH',
        '-dPDFSTOPONERROR=false',  # Continue on errors
        '-dAutoRotatePages=/None',  # Preserve page orientation
    ]

    # Add resolution if specified
    if resolution and resolution.isdigit():
        gs_command.extend([f'-r{resolution}'])

    # Metadata handling
    if retain_metadata:
        gs_command.extend(['-dPreserveAnnots=true'])
    else:
        gs_command.extend(['-dPreserveAnnots=false'])

    # Fast web view optimization
    if fast_mode:
        gs_command.extend(['-dFastWebView=true'])

    # Add input and output files
    gs_command.extend([f'-sOutputFile={output_path}', input_path])

    logging.debug(f"Ghostscript command: {' '.join(gs_command)}")

    # Run Ghostscript
    result = subprocess.run(gs_command, capture_output=True, text=True)

    if result.returncode != 0:
        logging.error(f"Ghostscript error: {result.stderr}")
        raise Exception(f"PDF compression failed: {result.stderr}")

    return result

@compress_bp.route('/compress', methods=['POST'])
def compress():
    """Handle PDF compression requests"""
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
        compression_level = request.form.get('compression_level', 'medium')
        retain_metadata = request.form.get('retain_metadata', 'true').lower() == 'true'
        resolution = request.form.get('resolution', '')
        fast_mode = request.form.get('fast_mode', 'false').lower() == 'true'

        # Validate compression level
        if compression_level not in ['high', 'medium', 'low', 'lossless']:
            compression_level = 'medium'

        # Create secure filenames
        original_filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())[:8]
        input_filename = f"{unique_id}_{original_filename}"
        output_filename = f"compressed_{compression_level}_{unique_id}_{original_filename}"

        input_path = os.path.join(STATIC_DIR, input_filename)
        output_path = os.path.join(STATIC_DIR, output_filename)

        # Save uploaded file
        file.save(input_path)
        logging.debug(f"File saved to: {input_path}")

        # Get original file size
        original_size = get_file_size(input_path)

        try:
            # Compress PDF
            compress_pdf(
                input_path,
                output_path,
                quality=compression_level,
                retain_metadata=retain_metadata,
                resolution=resolution,
                fast_mode=fast_mode
            )

            # Check if output file was created
            if not os.path.exists(output_path):
                raise Exception("Compression failed - no output file generated")

            # Get compressed file size
            compressed_size = get_file_size(output_path)

            # Calculate compression ratio
            if original_size > 0:
                compression_ratio = ((original_size - compressed_size) / original_size) * 100
            else:
                compression_ratio = 0

            logging.info(f"Compression completed: {original_size} -> {compressed_size} bytes ({compression_ratio:.1f}% reduction)")

            # Clean up input file
            try:
                os.remove(input_path)
            except OSError:
                pass

            # Return compressed file
            return send_file(
                output_path,
                as_attachment=True,
                download_name=f"compressed_{original_filename}",
                mimetype='application/pdf'
            )

        except subprocess.CalledProcessError as e:
            logging.error(f"Ghostscript subprocess error: {e}")
            return jsonify({"error": "PDF compression failed. The file may be corrupted or invalid."}), 500
        except Exception as e:
            logging.error(f"Compression error: {str(e)}")
            return jsonify({"error": f"Compression failed: {str(e)}"}), 500
        finally:
            # Clean up input file if it still exists
            if os.path.exists(input_path):
                try:
                    os.remove(input_path)
                except OSError:
                    pass

    except Exception as e:
        logging.error(f"Request handling error: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500
