from flask import Blueprint, request, send_file, jsonify
import fitz  # PyMuPDF
import os
import logging
import shutil
import math
import tempfile
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

watermark_bp = Blueprint('watermark', __name__)

STATIC_DIR = os.path.join(os.getcwd(), 'pdf_to_image', 'static')

# Ensure the static directory exists
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

# Color mapping for text watermarks
COLOR_MAP = {
    'gray': (128, 128, 128),
    'black': (0, 0, 0),
    'red': (255, 0, 0),
    'blue': (0, 0, 255),
    'green': (0, 128, 0)
}

def get_position_coordinates(position, page_width, page_height, content_width, content_height, margin=30):
    """Calculate x, y coordinates based on position string"""
    positions = {
        'center': ((page_width - content_width) / 2, (page_height - content_height) / 2),
        'top_left': (margin, margin),
        'top_center': ((page_width - content_width) / 2, margin),
        'top_right': (page_width - content_width - margin, margin),
        'middle_left': (margin, (page_height - content_height) / 2),
        'middle_right': (page_width - content_width - margin, (page_height - content_height) / 2),
        'bottom_left': (margin, page_height - content_height - margin),
        'bottom_center': ((page_width - content_width) / 2, page_height - content_height - margin),
        'bottom_right': (page_width - content_width - margin, page_height - content_height - margin),
        'diagonal': (margin, margin)  # Will be handled specially for diagonal watermarks
    }
    return positions.get(position, positions['center'])

def get_pages_to_process(pages_option, start_page, end_page, total_pages):
    """Determine which pages to process based on user selection"""
    if pages_option == 'all':
        return list(range(total_pages))
    elif pages_option == 'odd':
        return [i for i in range(total_pages) if (i + 1) % 2 == 1]
    elif pages_option == 'even':
        return [i for i in range(total_pages) if (i + 1) % 2 == 0]
    elif pages_option == 'first':
        return [0] if total_pages > 0 else []
    elif pages_option == 'range' and start_page and end_page:
        start = max(0, int(start_page) - 1)
        end = min(total_pages, int(end_page))
        return list(range(start, end))
    else:
        return list(range(total_pages))

@watermark_bp.route('/add_watermark', methods=['POST'])
def add_watermark():
    try:
        # Get form data
        file = request.files['file']
        watermark_type = request.form.get('watermark_type', 'text')
        position = request.form.get('position', 'center')
        watermark_text = request.form.get('watermark_text', 'Watermark')
        font_size = int(request.form.get('font_size', 36))
        opacity = int(request.form.get('opacity', 50))
        rotation = int(request.form.get('rotation', 0))
        text_color = request.form.get('text_color', 'gray')
        pages_to_watermark = request.form.get('pages_to_watermark', 'all')
        start_page = request.form.get('start_page')
        end_page = request.form.get('end_page')
        watermark_image = request.files.get('watermark_image')

        output_dir = os.path.join(STATIC_DIR, 'watermark')
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir, exist_ok=True)

        # Open PDF
        pdf = fitz.open(stream=file.read(), filetype='pdf')
        total_pages = pdf.page_count

        # Determine which pages to process
        pages_to_process = get_pages_to_process(pages_to_watermark, start_page, end_page, total_pages)

        for page_num in pages_to_process:
            page = pdf[page_num]
            if watermark_type == 'text':
                # Create an image with transparent background
                img_width = int(page.rect.width)
                img_height = int(page.rect.height)
                img = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)

                # Use a TrueType font
                font_paths = [
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                    "/System/Library/Fonts/Arial.ttf",  # macOS
                    "C:/Windows/Fonts/arial.ttf"  # Windows
                ]
                font = None
                for font_path in font_paths:
                    if os.path.exists(font_path):
                        try:
                            font = ImageFont.truetype(font_path, font_size)
                            break
                        except:
                            continue
                if font is None:
                    font = ImageFont.load_default()

                # Calculate text size using textbbox
                bbox = draw.textbbox((0, 0), watermark_text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]

                # Get color
                color = COLOR_MAP.get(text_color, COLOR_MAP['gray'])
                alpha = int(255 * (opacity / 100))
                fill_color = (*color, alpha)

                # Handle diagonal positioning
                if position == 'diagonal':
                    # Create a larger image for rotation
                    diagonal_size = int(math.sqrt(img_width**2 + img_height**2))
                    diagonal_img = Image.new('RGBA', (diagonal_size, diagonal_size), (0, 0, 0, 0))
                    diagonal_draw = ImageDraw.Draw(diagonal_img)

                    # Draw text in center of diagonal image
                    text_x = (diagonal_size - text_width) / 2
                    text_y = (diagonal_size - text_height) / 2
                    diagonal_draw.text((text_x, text_y), watermark_text, font=font, fill=fill_color)

                    # Rotate the image
                    angle = math.degrees(math.atan2(img_height, img_width))
                    rotated_img = diagonal_img.rotate(angle, expand=True)

                    # Paste onto main image
                    paste_x = (img_width - rotated_img.width) // 2
                    paste_y = (img_height - rotated_img.height) // 2
                    img.paste(rotated_img, (paste_x, paste_y), rotated_img)
                else:
                    # Get position coordinates
                    x, y = get_position_coordinates(position, img_width, img_height, text_width, text_height)

                    # Apply rotation if specified
                    if rotation != 0:
                        # Create temporary image for text
                        text_img = Image.new('RGBA', (text_width + 100, text_height + 100), (0, 0, 0, 0))
                        text_draw = ImageDraw.Draw(text_img)
                        text_draw.text((50, 50), watermark_text, font=font, fill=fill_color)

                        # Rotate text image
                        rotated_text = text_img.rotate(rotation, expand=True)

                        # Calculate new position after rotation
                        new_x = x - (rotated_text.width - text_width) // 2
                        new_y = y - (rotated_text.height - text_height) // 2

                        # Paste rotated text
                        img.paste(rotated_text, (int(new_x), int(new_y)), rotated_text)
                    else:
                        # Draw text directly
                        draw.text((x, y), watermark_text, font=font, fill=fill_color)

                # Save the image to a temporary path
                temp_img_path = os.path.join(output_dir, f'temp_text_watermark_{page_num}.png')
                img.save(temp_img_path, format='PNG')

                # Insert the image into the PDF page
                rect = fitz.Rect(0, 0, page.rect.width, page.rect.height)
                page.insert_image(rect, filename=temp_img_path, overlay=True)

            elif watermark_type in ['image', 'logo'] and watermark_image:
                img = Image.open(watermark_image).convert("RGBA")
                original_width, original_height = img.size

                # Scale image appropriately
                max_scale = 0.8 if watermark_type == 'image' else 0.3  # Logos should be smaller
                scale_factor = min(page.rect.width / original_width, page.rect.height / original_height) * max_scale
                new_width = int(original_width * scale_factor)
                new_height = int(original_height * scale_factor)
                img = img.resize((new_width, new_height), Image.LANCZOS)

                # Apply opacity
                if img.mode == 'RGBA':
                    alpha = img.split()[3]
                    alpha = ImageEnhance.Brightness(alpha).enhance(opacity / 100)
                    img.putalpha(alpha)
                else:
                    # Convert to RGBA and apply opacity
                    img = img.convert('RGBA')
                    alpha = Image.new('L', img.size, int(255 * (opacity / 100)))
                    img.putalpha(alpha)

                # Apply rotation if specified
                if rotation != 0:
                    img = img.rotate(rotation, expand=True)
                    new_width, new_height = img.size

                # Get position coordinates
                if position == 'diagonal':
                    # For diagonal, place along the diagonal
                    x = page.rect.width * 0.1
                    y = page.rect.height * 0.1
                else:
                    x, y = get_position_coordinates(position, page.rect.width, page.rect.height, new_width, new_height)

                # Save image and insert into PDF
                img_path = os.path.join(output_dir, f'temp_watermark_{page_num}.png')
                img.save(img_path)

                rect = fitz.Rect(x, y, x + new_width, y + new_height)
                page.insert_image(rect, filename=img_path, overlay=True)

        # Save the watermarked PDF
        output_path = os.path.join(output_dir, f'watermarked_{file.filename}')
        pdf.save(output_path)
        pdf.close()

        # Clean up temporary files
        for temp_file in os.listdir(output_dir):
            if temp_file.startswith('temp_'):
                try:
                    os.remove(os.path.join(output_dir, temp_file))
                except:
                    pass

        return send_file(output_path, as_attachment=True)

    except Exception as e:
        logging.error(f"Error adding watermark: {e}")
        return jsonify({"error": f"Failed to add watermark to PDF: {str(e)}"}), 500
