from flask import Blueprint, request, send_file, jsonify
import os
import subprocess
import tempfile
import logging
import shutil

logging.basicConfig(level=logging.DEBUG)

rotate_bp = Blueprint('rotate', __name__)

STATIC_DIR = os.path.join(os.getcwd(), 'pdf_to_image', 'static')

# Ensure the static directory exists
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

def rotate_pdf_pages_ghostscript(input_path, output_path, rotation_angle, pages_to_rotate=None):
    """
    Rotate PDF pages using Ghostscript
    """
    try:
        if pages_to_rotate is None:
            # Rotate all pages
            rotate_command = [
                'gs', '-sDEVICE=pdfwrite',
                '-dNOPAUSE', '-dQUIET', '-dBATCH',
                f'-dAutoRotatePages=/None',
                f'-sOutputFile={output_path}',
                input_path
            ]

            # Add rotation parameter
            if rotation_angle == 90:
                rotate_command.insert(-2, '-dRotatePages=1')
            elif rotation_angle == 180:
                rotate_command.insert(-2, '-dRotatePages=2')
            elif rotation_angle == 270:
                rotate_command.insert(-2, '-dRotatePages=3')

            subprocess.run(rotate_command, check=True)
        else:
            # Rotate specific pages - need to split, rotate, and merge
            temp_dir = tempfile.mkdtemp()

            # First, split PDF into individual pages
            split_command = [
                'gs', '-sDEVICE=pdfwrite',
                '-dNOPAUSE', '-dQUIET', '-dBATCH',
                '-sOutputFile={}/page_%d.pdf'.format(temp_dir),
                input_path
            ]

            subprocess.run(split_command, check=True)

            # Get total page count
            total_pages = get_pdf_page_count(input_path)

            # Rotate specific pages
            for page_num in pages_to_rotate:
                if 1 <= page_num <= total_pages:
                    page_file = os.path.join(temp_dir, f'page_{page_num}.pdf')
                    rotated_file = os.path.join(temp_dir, f'rotated_page_{page_num}.pdf')

                    if os.path.exists(page_file):
                        rotate_command = [
                            'gs', '-sDEVICE=pdfwrite',
                            '-dNOPAUSE', '-dQUIET', '-dBATCH',
                            f'-dAutoRotatePages=/None',
                            f'-sOutputFile={rotated_file}',
                            page_file
                        ]

                        # Add rotation parameter
                        if rotation_angle == 90:
                            rotate_command.insert(-2, '-dRotatePages=1')
                        elif rotation_angle == 180:
                            rotate_command.insert(-2, '-dRotatePages=2')
                        elif rotation_angle == 270:
                            rotate_command.insert(-2, '-dRotatePages=3')

                        subprocess.run(rotate_command, check=True)

                        # Replace original with rotated
                        os.replace(rotated_file, page_file)

            # Merge all pages back together
            page_files = []
            for i in range(1, total_pages + 1):
                page_file = os.path.join(temp_dir, f'page_{i}.pdf')
                if os.path.exists(page_file):
                    page_files.append(page_file)

            merge_command = [
                'gs', '-sDEVICE=pdfwrite',
                '-dNOPAUSE', '-dQUIET', '-dBATCH',
                '-sOutputFile={}'.format(output_path)
            ] + page_files

            subprocess.run(merge_command, check=True)

            # Clean up temporary files
            shutil.rmtree(temp_dir)

        return True

    except subprocess.CalledProcessError as e:
        logging.error(f"Ghostscript error: {e}")
        return False
    except Exception as e:
        logging.error(f"Error rotating PDF: {e}")
        return False

def get_pdf_page_count(pdf_path):
    """
    Get the number of pages in a PDF using Ghostscript
    """
    try:
        result = subprocess.run([
            'gs', '-q', '-dNODISPLAY', '-dBATCH',
            '-c', f'({pdf_path}) (r) file runpdfbegin pdfpagecount = quit'
        ], capture_output=True, text=True, check=True)

        return int(result.stdout.strip())
    except:
        return 0
@rotate_bp.route('/rotate', methods=['POST'])
def rotate_pages():
    try:
        file = request.files['file']
        rotation_angle = int(request.form.get('rotation_angle', 90))
        rotation_scope = request.form.get('rotation_scope', 'all_pages')
        pages_to_rotate = request.form.get('pages_to_rotate', '')

        if not file or file.filename == '':
            return jsonify({"error": "No file uploaded"}), 400

        # Validate rotation angle
        if rotation_angle not in [90, 180, 270]:
            return jsonify({"error": "Invalid rotation angle. Must be 90, 180, or 270 degrees"}), 400

        # Save uploaded file
        input_path = os.path.join(STATIC_DIR, f'input_{file.filename}')
        file.save(input_path)

        # Determine which pages to rotate
        pages_list = None
        if rotation_scope == 'specific_pages' and pages_to_rotate:
            try:
                pages_list = []
                for page_spec in pages_to_rotate.split(','):
                    page_spec = page_spec.strip()
                    if '-' in page_spec:
                        # Handle page ranges like "1-5"
                        start, end = map(int, page_spec.split('-'))
                        pages_list.extend(range(start, end + 1))
                    else:
                        # Handle individual pages
                        pages_list.append(int(page_spec))

                # Remove duplicates and sort
                pages_list = sorted(list(set(pages_list)))

            except ValueError:
                return jsonify({"error": "Invalid page specification"}), 400

        # Create output file
        rotation_desc = f"{rotation_angle}deg"
        if pages_list:
            rotation_desc += f"_pages_{'-'.join(map(str, pages_list[:3]))}"
            if len(pages_list) > 3:
                rotation_desc += "_etc"
        else:
            rotation_desc += "_all"

        output_filename = f'rotated_{rotation_desc}_{file.filename}'
        output_path = os.path.join(STATIC_DIR, output_filename)

        # Rotate pages using Ghostscript
        success = rotate_pdf_pages_ghostscript(input_path, output_path, rotation_angle, pages_list)

        if not success:
            return jsonify({"error": "Failed to rotate PDF pages"}), 500

        # Clean up input file
        os.remove(input_path)

        return send_file(output_path, as_attachment=True, download_name=output_filename)

    except Exception as e:
        logging.error(f"Error in rotate_pages: {e}")
        return jsonify({"error": str(e)}), 500

