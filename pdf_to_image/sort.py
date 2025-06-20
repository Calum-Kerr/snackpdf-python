from flask import Blueprint, request, send_file, jsonify
import os
import subprocess
import tempfile
import logging
import shutil

logging.basicConfig(level=logging.DEBUG)

sort_bp = Blueprint('sort', __name__)

STATIC_DIR = os.path.join(os.getcwd(), 'pdf_to_image', 'static')

# Ensure the static directory exists
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

def sort_pdf_pages_ghostscript(input_path, output_path, page_order):
    """
    Sort PDF pages using Ghostscript
    """
    try:
        # Create temporary directory for individual pages
        temp_dir = tempfile.mkdtemp()

        # First, split PDF into individual pages
        split_command = [
            'gs', '-sDEVICE=pdfwrite',
            '-dNOPAUSE', '-dQUIET', '-dBATCH',
            '-sOutputFile={}/page_%d.pdf'.format(temp_dir),
            input_path
        ]

        subprocess.run(split_command, check=True)

        # Get list of created page files
        page_files = []
        for page_num in page_order:
            page_file = os.path.join(temp_dir, f'page_{page_num}.pdf')
            if os.path.exists(page_file):
                page_files.append(page_file)
            else:
                logging.warning(f"Page {page_num} not found, skipping")

        if not page_files:
            raise Exception("No valid pages found to sort")

        # Merge pages in the specified order
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
        logging.error(f"Error sorting PDF: {e}")
        return False

def generate_page_order(method, total_pages, custom_order=None):
    """
    Generate page order based on sorting method
    """
    if method == 'custom_order' and custom_order:
        try:
            return [int(x.strip()) for x in custom_order.split(',') if x.strip().isdigit()]
        except:
            return list(range(1, total_pages + 1))

    elif method == 'reverse_order':
        return list(range(total_pages, 0, -1))

    elif method == 'odd_even':
        odd_pages = [i for i in range(1, total_pages + 1) if i % 2 == 1]
        even_pages = [i for i in range(1, total_pages + 1) if i % 2 == 0]
        return odd_pages + even_pages

    elif method == 'even_odd':
        odd_pages = [i for i in range(1, total_pages + 1) if i % 2 == 1]
        even_pages = [i for i in range(1, total_pages + 1) if i % 2 == 0]
        return even_pages + odd_pages

    elif method == 'interleave':
        odd_pages = [i for i in range(1, total_pages + 1) if i % 2 == 1]
        even_pages = [i for i in range(1, total_pages + 1) if i % 2 == 0]
        return odd_pages + even_pages

    elif method == 'booklet':
        # Booklet order: n, 1, 2, n-1, n-2, 3, 4, n-3, ...
        order = []
        front = 1
        back = total_pages
        while front <= back:
            if len(order) % 4 == 0:
                order.extend([back, front])
            else:
                order.extend([front, back])
            front += 1
            back -= 1
        return order[:total_pages]

    else:
        return list(range(1, total_pages + 1))

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
@sort_bp.route('/sort', methods=['POST'])
def sort_pages():
    try:
        file = request.files['file']
        sort_method = request.form.get('sort_method', 'custom_order')
        custom_order = request.form.get('page_order', '')
        duplicate_handling = request.form.get('duplicate_handling', 'allow')
        missing_pages = request.form.get('missing_pages', 'skip')

        if not file or file.filename == '':
            return jsonify({"error": "No file uploaded"}), 400

        # Save uploaded file
        input_path = os.path.join(STATIC_DIR, f'input_{file.filename}')
        file.save(input_path)

        # Get page count
        total_pages = get_pdf_page_count(input_path)
        if total_pages == 0:
            return jsonify({"error": "Could not determine PDF page count"}), 400

        # Generate page order
        page_order = generate_page_order(sort_method, total_pages, custom_order)

        if not page_order:
            return jsonify({"error": "Invalid page order specified"}), 400

        # Handle duplicates
        if duplicate_handling == 'remove':
            seen = set()
            page_order = [x for x in page_order if not (x in seen or seen.add(x))]

        # Filter out invalid pages
        valid_page_order = [p for p in page_order if 1 <= p <= total_pages]

        if not valid_page_order:
            return jsonify({"error": "No valid pages in the specified order"}), 400

        # Create output file
        output_filename = f'sorted_{sort_method}_{file.filename}'
        output_path = os.path.join(STATIC_DIR, output_filename)

        # Sort pages using Ghostscript
        success = sort_pdf_pages_ghostscript(input_path, output_path, valid_page_order)

        if not success:
            return jsonify({"error": "Failed to sort PDF pages"}), 500

        # Clean up input file
        os.remove(input_path)

        return send_file(output_path, as_attachment=True, download_name=output_filename)

    except Exception as e:
        logging.error(f"Error in sort_pages: {e}")
        return jsonify({"error": str(e)}), 500
