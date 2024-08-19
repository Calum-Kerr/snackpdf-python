from flask import Blueprint, request, send_file, jsonify
import os
import subprocess

compress_bp = Blueprint('compress_bp', __name__)
STATIC_DIR = os.path.join(os.getcwd(), 'pdf_to_image', 'static')

def compress_pdf(input_path, output_path, quality, retain_metadata, lossless, resolution, fast_mode):
    quality_settings = {
        'high': '/screen',
        'medium': '/ebook',
        'low': '/prepress',
        'lossless': '/prepress'
    }
    gs_quality = quality_settings.get(quality, '/screen')

    gs_command = [
        'gs', '-sDEVICE=pdfwrite',
        '-dCompatibilityLevel=1.4',
        '-dPDFSETTINGS={}'.format(gs_quality),
        '-dNOPAUSE', '-dQUIET', '-dBATCH',
    ]

    if resolution:
        gs_command.extend(['-r{}'.format(resolution)])

    if not retain_metadata:
        gs_command.extend(['-dUseCIEColor'])

    if lossless:
        gs_command.extend(['-dEncodeColorImages=false', '-dEncodeGrayImages=false', '-dEncodeMonoImages=false'])

    if fast_mode:
        gs_command.extend(['-dFastWebView=true'])

    gs_command.extend(['-sOutputFile={}'.format(output_path), input_path])

    subprocess.run(gs_command, check=True)

@compress_bp.route('/compress', methods=['POST'])
def compress():
    files = request.files.getlist('files')
    compression_level = request.form.get('compression_level', 'medium')
    retain_metadata = request.form.get('retain_metadata', 'true').lower() == 'true'
    lossless = request.form.get('lossless', 'false').lower() == 'true'
    resolution = request.form.get('resolution', '')
    fast_mode = request.form.get('fast_mode', 'false').lower() == 'true'

    if len(files) == 0:
        return jsonify({"error": "No files uploaded"}), 400

    file = files[0]  # Assuming single file compression
    file_path = os.path.join(STATIC_DIR, file.filename)
    output_path = os.path.join(STATIC_DIR, f'compressed_{compression_level}_{file.filename}')
    file.save(file_path)

    try:
        compress_pdf(file_path, output_path, quality=compression_level, retain_metadata=retain_metadata,
                     lossless=lossless, resolution=resolution, fast_mode=fast_mode)

        return send_file(output_path, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
