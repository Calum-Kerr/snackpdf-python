from flask import Blueprint, request, send_file, jsonify
import fitz  # PyMuPDF
import os
import logging
import shutil
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

watermark_bp = Blueprint('watermark', __name__)

STATIC_DIR = os.path.join(os.getcwd(), 'pdf_to_image', 'static')

# Ensure the static directory exists
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

@watermark_bp.route('/add_watermark', methods=['POST'])
def add_watermark():
    file = request.files['file']
    watermark_type = request.form.get('watermark_type', 'text')
    position = request.form.get('position', 'center')
    watermark_text = request.form.get('watermark_text', 'Watermark')
    font_size = int(request.form.get('font_size', 36))
    watermark_image = request.files.get('watermark_image')
    output_dir = os.path.join(STATIC_DIR, 'watermark')

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    try:
        pdf = fitz.open(stream=file.read(), filetype='pdf')

        for page in pdf:
            if watermark_type == 'text':
                # Create an image with transparent background
                img_width = int(page.rect.width)
                img_height = int(page.rect.height)
                img = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)

                # Use a TrueType font
                font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"  # Adjust the font path as needed
                if not os.path.exists(font_path):
                    # Fallback to a default font
                    font = ImageFont.load_default()
                else:
                    font = ImageFont.truetype(font_path, font_size)

                # Calculate text size using textbbox
                bbox = draw.textbbox((0, 0), watermark_text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]

                if position == 'center':
                    x = (img_width - text_width) / 2
                    y = (img_height - text_height) / 2
                elif position == 'top':
                    x = (img_width - text_width) / 2
                    y = 30
                elif position == 'bottom':
                    x = (img_width - text_width) / 2
                    y = img_height - text_height - 30

                # Draw text onto the image with opacity
                draw.text(
                    (x, y),
                    watermark_text,
                    font=font,
                    fill=(128, 128, 128, int(255 * 0.3))  # 30% opacity
                )

                # Save the image to a temporary path
                temp_img_path = os.path.join(output_dir, 'temp_text_watermark.png')
                img.save(temp_img_path, format='PNG')

                # Insert the image into the PDF page
                rect = fitz.Rect(0, 0, page.rect.width, page.rect.height)
                page.insert_image(rect, filename=temp_img_path, overlay=True)

            elif watermark_type == 'image' and watermark_image:
                img = Image.open(watermark_image).convert("RGBA")
                img_width, img_height = img.size
                scale_factor = min(page.rect.width / img_width, page.rect.height / img_height) * 0.8
                img_width, img_height = int(img_width * scale_factor), int(img_height * scale_factor)
                img = img.resize((img_width, img_height), Image.LANCZOS)  # Use Image.LANCZOS instead of Image.ANTIALIAS

                if position == 'center':
                    x = (page.rect.width - img_width) / 2
                    y = (page.rect.height - img_height) / 2
                elif position == 'top':
                    x = (page.rect.width - img_width) / 2
                    y = 30
                elif position == 'bottom':
                    x = (page.rect.width - img_width) / 2
                    y = page.rect.height - img_height - 30

                # Adjust opacity
                alpha = img.split()[3]
                alpha = ImageEnhance.Brightness(alpha).enhance(0.3)
                img.putalpha(alpha)

                img_path = os.path.join(output_dir, 'temp_watermark.png')
                img.save(img_path)

                rect = fitz.Rect(x, y, x + img_width, y + img_height)
                page.insert_image(rect, filename=img_path, overlay=True)

        output_path = os.path.join(output_dir, f'watermarked_{file.filename}')
        pdf.save(output_path)
        pdf.close()

        return send_file(output_path, as_attachment=True)

    except Exception as e:
        logging.error(f"Error adding watermark: {e}")
        return jsonify({"error": "Failed to add watermark to PDF"}), 500
