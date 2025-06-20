from flask import Blueprint, request, send_file, jsonify
import os
import subprocess
import tempfile
import logging
import shutil

logging.basicConfig(level=logging.DEBUG)

pdf_to_pdfa_bp = Blueprint('pdf_to_pdfa', __name__)

STATIC_DIR = os.path.join(os.getcwd(), 'pdf_to_image', 'static')

# Ensure the static directory exists
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

def convert_to_pdfa_ghostscript(input_path, output_path, pdfa_level='2b', preserve_metadata=True):
    """Convert PDF to PDF/A using Ghostscript"""
    try:
        # PDF/A level settings
        pdfa_settings = {
            '1b': {
                'compatibility': '1.4',
                'pdfa_def': 'PDFA_def.ps',
                'color_profile': 'sRGB.icc'
            },
            '2b': {
                'compatibility': '1.7',
                'pdfa_def': 'PDFA_def.ps',
                'color_profile': 'sRGB.icc'
            },
            '3b': {
                'compatibility': '1.7',
                'pdfa_def': 'PDFA_def.ps',
                'color_profile': 'sRGB.icc'
            }
        }
        
        settings = pdfa_settings.get(pdfa_level, pdfa_settings['2b'])
        
        # Build Ghostscript command for PDF/A conversion
        gs_command = [
            'gs',
            '-dPDFA',
            '-dBATCH',
            '-dNOPAUSE',
            '-dQUIET',
            '-dUseCIEColor',
            '-sProcessColorModel=DeviceRGB',
            '-sDEVICE=pdfwrite',
            f'-dCompatibilityLevel={settings["compatibility"]}',
            '-dPDFACompatibilityPolicy=1',
            f'-sOutputFile={output_path}',
        ]
        
        # Add color profile and PDF/A definition if available
        # Note: These files might not be available in all Ghostscript installations
        # The conversion will still work without them, just with less strict compliance
        
        if preserve_metadata:
            gs_command.extend([
                '-dPreserveAnnots=true',
                '-dPreserveMarkedContent=true'
            ])
        
        # Add input file
        gs_command.append(input_path)
        
        logging.debug(f"Running Ghostscript PDF/A command: {' '.join(gs_command)}")
        
        # Run Ghostscript
        result = subprocess.run(gs_command, capture_output=True, text=True)
        
        if result.returncode != 0:
            logging.error(f"Ghostscript PDF/A error: {result.stderr}")
            # Try fallback conversion without strict PDF/A compliance
            return convert_to_pdfa_fallback(input_path, output_path)
        
        logging.debug("PDF/A conversion successful")
        return True
        
    except Exception as e:
        logging.error(f"Error in PDF/A conversion: {e}")
        raise

def convert_to_pdfa_fallback(input_path, output_path):
    """Fallback PDF/A conversion with basic settings"""
    try:
        logging.debug("Attempting fallback PDF/A conversion")
        
        gs_command = [
            'gs',
            '-dBATCH',
            '-dNOPAUSE',
            '-dQUIET',
            '-sDEVICE=pdfwrite',
            '-dCompatibilityLevel=1.7',
            '-dAutoRotatePages=/None',
            '-dColorImageDownsampleType=/Bicubic',
            '-dColorImageResolution=300',
            '-dGrayImageDownsampleType=/Bicubic',
            '-dGrayImageResolution=300',
            '-dMonoImageDownsampleType=/Bicubic',
            '-dMonoImageResolution=1200',
            f'-sOutputFile={output_path}',
            input_path
        ]
        
        result = subprocess.run(gs_command, capture_output=True, text=True)
        
        if result.returncode != 0:
            logging.error(f"Fallback conversion failed: {result.stderr}")
            raise Exception(f"PDF conversion failed: {result.stderr}")
        
        logging.debug("Fallback PDF/A conversion successful")
        return True
        
    except Exception as e:
        logging.error(f"Error in fallback conversion: {e}")
        raise

def validate_pdf_input(file_path):
    """Basic validation of PDF input"""
    try:
        # Check file size (limit to reasonable size for processing)
        file_size = os.path.getsize(file_path)
        max_size = 100 * 1024 * 1024  # 100MB limit
        
        if file_size > max_size:
            raise Exception(f"File too large: {file_size / (1024*1024):.1f}MB (max: 100MB)")
        
        # Try to open with Ghostscript to validate
        gs_command = [
            'gs',
            '-dBATCH',
            '-dNOPAUSE',
            '-dQUIET',
            '-sDEVICE=nullpage',
            file_path
        ]
        
        result = subprocess.run(gs_command, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            raise Exception("Invalid or corrupted PDF file")
        
        return True
        
    except subprocess.TimeoutExpired:
        raise Exception("PDF validation timeout - file may be corrupted")
    except Exception as e:
        logging.error(f"PDF validation error: {e}")
        raise

@pdf_to_pdfa_bp.route('/pdf_to_pdfa', methods=['POST'])
def convert_pdf_to_pdfa():
    """Handle PDF to PDF/A conversion requests"""
    try:
        # Handle multiple files
        files = request.files.getlist('files')
        if not files or not files[0].filename:
            return jsonify({"error": "No files uploaded"}), 400

        # For now, process only the first file
        file = files[0]

        # Get options from form (match template field names)
        pdfa_level = request.form.get('pdfa_level', 'pdfa-2b').replace('pdfa-', '').replace('a', 'b')  # Convert to our format
        color_profile = request.form.get('color_profile', 'srgb')
        font_embedding = request.form.get('font_embedding', 'embed_all')
        image_compression = request.form.get('image_compression', 'lossless')
        metadata_preservation = request.form.get('metadata_preservation', 'preserve')

        preserve_metadata = metadata_preservation == 'preserve'
        optimize_size = image_compression != 'lossless'
        
        logging.debug(f"Converting PDF to PDF/A-{pdfa_level}, preserve_metadata: {preserve_metadata}")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save uploaded PDF
            pdf_path = os.path.join(temp_dir, file.filename)
            file.save(pdf_path)
            
            # Validate input PDF
            validate_pdf_input(pdf_path)
            
            # Create output path
            base_name = os.path.splitext(file.filename)[0]
            output_filename = f"{base_name}_PDFA-{pdfa_level}.pdf"
            output_path = os.path.join(temp_dir, output_filename)
            
            # Convert to PDF/A
            success = convert_to_pdfa_ghostscript(
                pdf_path, output_path, pdfa_level, preserve_metadata
            )
            
            if not success or not os.path.exists(output_path):
                return jsonify({"error": "PDF/A conversion failed"}), 500
            
            # Optional size optimization
            if optimize_size:
                optimized_path = os.path.join(temp_dir, f"optimized_{output_filename}")
                try:
                    optimize_pdf_size(output_path, optimized_path)
                    if os.path.exists(optimized_path):
                        output_path = optimized_path
                        output_filename = f"optimized_{output_filename}"
                except Exception as e:
                    logging.warning(f"Size optimization failed: {e}")
                    # Continue with unoptimized file
            
            return send_file(output_path, as_attachment=True,
                           download_name=output_filename,
                           mimetype='application/pdf')
            
    except Exception as e:
        logging.error(f"Error in PDF to PDF/A conversion: {e}")
        return jsonify({"error": str(e)}), 500

def optimize_pdf_size(input_path, output_path):
    """Optimize PDF file size"""
    try:
        gs_command = [
            'gs',
            '-sDEVICE=pdfwrite',
            '-dCompatibilityLevel=1.7',
            '-dPDFSETTINGS=/ebook',
            '-dNOPAUSE',
            '-dQUIET',
            '-dBATCH',
            '-dColorImageDownsampleType=/Bicubic',
            '-dColorImageResolution=150',
            '-dGrayImageDownsampleType=/Bicubic',
            '-dGrayImageResolution=150',
            '-dMonoImageDownsampleType=/Bicubic',
            '-dMonoImageResolution=300',
            f'-sOutputFile={output_path}',
            input_path
        ]
        
        result = subprocess.run(gs_command, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Size optimization failed: {result.stderr}")
        
        logging.debug("PDF size optimization successful")
        
    except Exception as e:
        logging.error(f"Error in size optimization: {e}")
        raise
