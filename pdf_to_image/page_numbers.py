from flask import Blueprint, request, send_file, jsonify
import fitz  # PyMuPDF
import os
import logging
import shutil
import tempfile

page_numbers_bp = Blueprint('page_numbers', __name__)

STATIC_DIR = os.path.join(os.getcwd(), 'pdf_to_image', 'static')

# Ensure the static directory exists
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

# Color mapping for page numbers
COLOR_MAP = {
    'black': (0, 0, 0),
    'gray': (0.5, 0.5, 0.5),
    'blue': (0, 0, 1),
    'red': (1, 0, 0)
}

def format_page_number(page_num, number_format, total_pages, custom_format=None):
    """Format page number according to specified format"""
    if number_format == '1':
        return str(page_num)
    elif number_format == 'i':
        return int_to_roman(page_num).lower()
    elif number_format == 'I':
        return int_to_roman(page_num).upper()
    elif number_format == 'a':
        return int_to_letter(page_num).lower()
    elif number_format == 'A':
        return int_to_letter(page_num).upper()
    elif number_format == 'page_of_total':
        return f"Page {page_num} of {total_pages}"
    elif number_format == 'custom' and custom_format:
        return custom_format.replace('{n}', str(page_num)).replace('{total}', str(total_pages))
    else:
        return str(page_num)

def int_to_roman(num):
    """Convert integer to Roman numeral"""
    values = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
    literals = ['M', 'CM', 'D', 'CD', 'C', 'XC', 'L', 'XL', 'X', 'IX', 'V', 'IV', 'I']
    roman = ''
    for i in range(len(values)):
        count = num // values[i]
        roman += literals[i] * count
        num -= values[i] * count
    return roman

def int_to_letter(num):
    """Convert integer to letter (A, B, C, ... Z, AA, BB, etc.)"""
    result = ''
    while num > 0:
        num -= 1
        result = chr(65 + (num % 26)) + result
        num //= 26
    return result

def get_margin_value(margin_setting):
    """Convert margin setting to point value"""
    margins = {
        'small': 10,
        'medium': 20,
        'large': 30
    }
    return margins.get(margin_setting, 20)

def get_pages_to_number(pages_option, start_page, end_page, total_pages):
    """Determine which pages to number based on user selection"""
    if pages_option == 'all':
        return list(range(1, total_pages + 1))
    elif pages_option == 'odd':
        return [i for i in range(1, total_pages + 1) if i % 2 == 1]
    elif pages_option == 'even':
        return [i for i in range(1, total_pages + 1) if i % 2 == 0]
    elif pages_option == 'range' and start_page and end_page:
        start = max(1, int(start_page))
        end = min(total_pages, int(end_page))
        return list(range(start, end + 1))
    elif pages_option == 'exclude_first':
        return list(range(2, total_pages + 1))
    else:
        return list(range(1, total_pages + 1))

@page_numbers_bp.route('/add_page_numbers', methods=['POST'])
def add_page_numbers():
    try:
        # Get form data
        file = request.files['file']
        position = request.form.get('position', 'bottom_center')
        number_format = request.form.get('number_format', '1')
        custom_format = request.form.get('custom_format', '')
        start_number = int(request.form.get('start_number', 1))
        font_size = int(request.form.get('font_size', 12))
        font_color = request.form.get('font_color', 'black')
        margin = request.form.get('margin', 'medium')
        pages_to_number = request.form.get('pages_to_number', 'all')
        start_page = request.form.get('start_page')
        end_page = request.form.get('end_page')

        output_dir = os.path.join(STATIC_DIR, 'page_numbers')
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir, exist_ok=True)

        # Open PDF
        pdf = fitz.open(stream=file.read(), filetype='pdf')
        total_pages = pdf.page_count

        # Determine which pages to number
        pages_to_process = get_pages_to_number(pages_to_number, start_page, end_page, total_pages)

        # Get margin value
        margin_value = get_margin_value(margin)

        # Get color
        color = COLOR_MAP.get(font_color, COLOR_MAP['black'])

        for page_index in range(total_pages):
            page = pdf[page_index]
            page_num = page_index + 1

            # Skip pages not in the list to process
            if page_num not in pages_to_process:
                continue

            # Calculate the actual page number to display (considering start_number)
            display_number = page_num - min(pages_to_process) + start_number

            # Format the page number
            formatted_number = format_page_number(display_number, number_format, total_pages, custom_format)

            # Calculate text dimensions
            text_rect = fitz.get_text_length(formatted_number, fontsize=font_size)

            # Calculate position coordinates
            rect = page.rect
            if position == 'bottom_center':
                x = (rect.width - text_rect) / 2
                y = rect.height - margin_value
            elif position == 'bottom_left':
                x = margin_value
                y = rect.height - margin_value
            elif position == 'bottom_right':
                x = rect.width - text_rect - margin_value
                y = rect.height - margin_value
            elif position == 'top_center':
                x = (rect.width - text_rect) / 2
                y = margin_value + font_size
            elif position == 'top_left':
                x = margin_value
                y = margin_value + font_size
            elif position == 'top_right':
                x = rect.width - text_rect - margin_value
                y = margin_value + font_size
            else:
                # Default to bottom center
                x = (rect.width - text_rect) / 2
                y = rect.height - margin_value

            # Insert the page number
            page.insert_text(
                (x, y),
                formatted_number,
                fontsize=font_size,
                color=color
            )

        # Save the PDF with page numbers
        output_path = os.path.join(output_dir, f'page_numbered_{file.filename}')
        pdf.save(output_path)
        pdf.close()

        return send_file(output_path, as_attachment=True)

    except Exception as e:
        logging.error(f"Error adding page numbers: {e}")
        return jsonify({"error": f"Failed to add page numbers to PDF: {str(e)}"}), 500

