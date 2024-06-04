from flask import Blueprint, request, send_file
import os
import subprocess

compress_bp = Blueprint('compress_bp', __name__)
STATIC_DIR = os.path.join(os.getcwd(), 'pdf_to_image', 'static')

def compress_pdf(input_path, output_path, quality):
    quality_settings = {
        'high': '/screen',
        'medium': '/ebook',
        'low': '/prepress'
    }
    gs_quality = quality_settings.get(quality, '/screen')

    # Ghostscript command to compress PDF
    gs_command = [
        'gs', '-sDEVICE=pdfwrite',
        '-dCompatibilityLevel=1.4',
        '-dPDFSETTINGS={}'.format(gs_quality),
        '-dNOPAUSE', '-dQUIET', '-dBATCH',
        '-sOutputFile={}'.format(output_path),
        input_path
    ]

    subprocess.run(gs_command, check=True)

@compress_bp.route('/compress', methods=['POST'])
def compress():
    file = request.files['file']
    compression_level = request.form.get('compression_level', 'medium')
    file_path = os.path.join(STATIC_DIR, file.filename)
    output_path = os.path.join(STATIC_DIR, f'compressed_{compression_level}_{file.filename}')
    file.save(file_path)

    compress_pdf(file_path, output_path, quality=compression_level)

    return send_file(output_path, as_attachment=True)
