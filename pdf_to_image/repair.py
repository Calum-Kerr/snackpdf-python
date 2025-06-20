from flask import Blueprint, request, send_file, jsonify
import os
import subprocess
import logging
import uuid
from werkzeug.utils import secure_filename

repair_bp = Blueprint('repair', __name__)

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

def repair_pdf_with_ghostscript(input_path, output_path, repair_level='standard', repair_options=None):
    """Repair PDF using Ghostscript with error recovery"""
    if repair_options is None:
        repair_options = {}

    # Base Ghostscript command for PDF repair
    gs_command = [
        'gs', '-sDEVICE=pdfwrite',
        '-dCompatibilityLevel=1.4',
        '-dPDFSETTINGS=/prepress',  # High quality for repair
        '-dNOPAUSE', '-dQUIET', '-dBATCH',
        '-dPDFSTOPONERROR=false',   # Continue processing on errors
        '-dAutoRotatePages=/None',  # Preserve page orientation
    ]

    # Repair level settings
    if repair_level == 'basic':
        # Basic repair - minimal error recovery
        gs_command.extend([
            '-dPDFSTOPONERROR=false',
        ])
    elif repair_level == 'standard':
        # Standard repair - moderate error recovery
        gs_command.extend([
            '-dPDFSTOPONERROR=false',
            '-dNOSAFER',  # Allow more operations for repair
        ])
    elif repair_level == 'aggressive':
        # Aggressive repair - maximum error recovery
        gs_command.extend([
            '-dPDFSTOPONERROR=false',
            '-dNOSAFER',
            '-dDOINTERPOLATE',  # Interpolate images
            '-dGraphicsAlphaBits=4',  # Anti-aliasing
            '-dTextAlphaBits=4',
        ])
    elif repair_level == 'deep_scan':
        # Deep scan repair - comprehensive reconstruction
        gs_command.extend([
            '-dPDFSTOPONERROR=false',
            '-dNOSAFER',
            '-dDOINTERPOLATE',
            '-dGraphicsAlphaBits=4',
            '-dTextAlphaBits=4',
            '-dUseCropBox=false',  # Use full page
        ])

    # Apply repair options from form
    if repair_options.get('fix_structure'):
        gs_command.extend(['-dPDFSTOPONERROR=false'])

    if repair_options.get('recover_images'):
        gs_command.extend(['-dDOINTERPOLATE'])

    if repair_options.get('fix_fonts'):
        gs_command.extend(['-dNOPLATFONTS'])

    if repair_options.get('rebuild_xref'):
        gs_command.extend(['-dFIXEDMEDIA'])

    # Add input and output files
    gs_command.extend([f'-sOutputFile={output_path}', input_path])

    logging.debug(f"Ghostscript repair command: {' '.join(gs_command)}")

    # Run Ghostscript
    result = subprocess.run(gs_command, capture_output=True, text=True)

    if result.returncode != 0:
        logging.error(f"Ghostscript repair error: {result.stderr}")
        # Don't raise exception immediately - some errors are recoverable
        if "Fatal" in result.stderr or "Error" in result.stderr:
            # Check if output file was still created
            if not os.path.exists(output_path):
                raise Exception(f"PDF repair failed: {result.stderr}")

    return result

@repair_bp.route('/repair', methods=['POST'])
def repair_pdf():
    """Handle PDF repair requests"""
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
        repair_level = request.form.get('repair_level', 'standard')

        # Get repair options from checkboxes
        repair_options = {
            'fix_structure': request.form.get('fix_structure') == 'yes',
            'recover_text': request.form.get('recover_text') == 'yes',
            'recover_images': request.form.get('recover_images') == 'yes',
            'fix_fonts': request.form.get('fix_fonts') == 'yes',
            'rebuild_xref': request.form.get('rebuild_xref') == 'yes',
            'remove_corruption': request.form.get('remove_corruption') == 'yes',
        }

        # Validate repair level
        if repair_level not in ['basic', 'standard', 'aggressive', 'deep_scan']:
            repair_level = 'standard'

        # Create secure filenames
        original_filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())[:8]
        input_filename = f"{unique_id}_{original_filename}"
        output_filename = f"repaired_{repair_level}_{unique_id}_{original_filename}"

        input_path = os.path.join(STATIC_DIR, input_filename)
        output_path = os.path.join(STATIC_DIR, output_filename)

        # Save uploaded file
        file.save(input_path)
        logging.debug(f"File saved to: {input_path}")

        try:
            # Repair PDF
            repair_pdf_with_ghostscript(
                input_path,
                output_path,
                repair_level=repair_level,
                repair_options=repair_options
            )

            # Check if output file was created
            if not os.path.exists(output_path):
                raise Exception("Repair failed - no output file generated")

            # Get file sizes for reporting
            original_size = os.path.getsize(input_path) if os.path.exists(input_path) else 0
            repaired_size = os.path.getsize(output_path)

            logging.info(f"Repair completed: {original_size} -> {repaired_size} bytes")

            # Clean up input file
            try:
                os.remove(input_path)
            except OSError:
                pass

            # Return repaired file
            return send_file(
                output_path,
                as_attachment=True,
                download_name=f"repaired_{original_filename}",
                mimetype='application/pdf'
            )

        except subprocess.CalledProcessError as e:
            logging.error(f"Ghostscript subprocess error: {e}")
            return jsonify({"error": "PDF repair failed. The file may be severely corrupted."}), 500
        except Exception as e:
            logging.error(f"Repair error: {str(e)}")
            return jsonify({"error": f"Repair failed: {str(e)}"}), 500
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

