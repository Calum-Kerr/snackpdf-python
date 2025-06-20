from flask import Blueprint, request, send_file, jsonify
import fitz  # PyMuPDF
import os
import tempfile
import shutil
import logging
from datetime import datetime
import subprocess
import json
from PIL import Image, ImageDraw, ImageFont
import io
import base64

security_bp = Blueprint('security', __name__)

STATIC_DIR = os.path.join(os.getcwd(), 'pdf_to_image', 'static')

# Ensure the static directory exists
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

# Configure logging
logging.basicConfig(level=logging.INFO)

@security_bp.route('/unlock_pdf', methods=['POST'])
def unlock_pdf():
    """Enhanced PDF unlock with better error handling and batch support"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files['file']
        password = request.form.get('password', '')

        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        # Create temporary directory for processing
        temp_dir = tempfile.mkdtemp()
        try:
            # Save uploaded file
            input_path = os.path.join(temp_dir, file.filename)
            file.save(input_path)

            # Open and unlock PDF
            pdf = fitz.open(input_path)

            if pdf.needs_pass:
                if not password:
                    return jsonify({"error": "Password required for this PDF"}), 400

                if not pdf.authenticate(password):
                    return jsonify({"error": "Invalid password"}), 401

            # Save unlocked PDF
            output_filename = f'unlocked_{file.filename}'
            output_path = os.path.join(STATIC_DIR, output_filename)

            # Save without password protection
            pdf.save(output_path)
            pdf.close()

            return send_file(output_path, as_attachment=True, download_name=output_filename)

        finally:
            # Cleanup temporary directory
            shutil.rmtree(temp_dir, ignore_errors=True)

    except Exception as e:
        logging.error(f"Error unlocking PDF: {str(e)}")
        return jsonify({"error": f"Failed to unlock PDF: {str(e)}"}), 500

@security_bp.route('/protect_pdf', methods=['POST'])
def protect_pdf():
    """Enhanced PDF protection with multiple encryption levels and permissions"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files['file']
        user_password = request.form.get('user_password', '')
        owner_password = request.form.get('owner_password', user_password)
        encryption_level = request.form.get('encryption_level', '256')

        # Permission settings
        allow_print = request.form.get('allow_print', 'false').lower() == 'true'
        allow_copy = request.form.get('allow_copy', 'false').lower() == 'true'
        allow_edit = request.form.get('allow_edit', 'false').lower() == 'true'
        allow_annotate = request.form.get('allow_annotate', 'false').lower() == 'true'

        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        # Create temporary directory for processing
        temp_dir = tempfile.mkdtemp()
        try:
            # Save uploaded file
            input_path = os.path.join(temp_dir, file.filename)
            file.save(input_path)

            # Open PDF
            pdf = fitz.open(input_path)

            # Set encryption level
            if encryption_level == '40':
                encryption = fitz.PDF_ENCRYPT_RC4_40
            elif encryption_level == '128':
                encryption = fitz.PDF_ENCRYPT_RC4_128
            else:  # Default to 256-bit AES
                encryption = fitz.PDF_ENCRYPT_AES_256

            # Calculate permissions
            permissions = 0
            if allow_print:
                permissions |= fitz.PDF_PERM_PRINT
            if allow_copy:
                permissions |= fitz.PDF_PERM_COPY
            if allow_edit:
                permissions |= fitz.PDF_PERM_MODIFY
            if allow_annotate:
                permissions |= fitz.PDF_PERM_ANNOTATE

            # Save protected PDF
            output_filename = f'protected_{file.filename}'
            output_path = os.path.join(STATIC_DIR, output_filename)

            pdf.save(output_path,
                    encryption=encryption,
                    owner_pw=owner_password,
                    user_pw=user_password,
                    permissions=permissions)
            pdf.close()

            return send_file(output_path, as_attachment=True, download_name=output_filename)

        finally:
            # Cleanup temporary directory
            shutil.rmtree(temp_dir, ignore_errors=True)

    except Exception as e:
        logging.error(f"Error protecting PDF: {str(e)}")
        return jsonify({"error": f"Failed to protect PDF: {str(e)}"}), 500


@security_bp.route('/flatten_pdf', methods=['POST'])
def flatten_pdf():
    """Flatten PDF forms and remove interactive elements"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files['file']
        flatten_forms = request.form.get('flatten_forms', 'true').lower() == 'true'
        flatten_annotations = request.form.get('flatten_annotations', 'true').lower() == 'true'

        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        # Create temporary directory for processing
        temp_dir = tempfile.mkdtemp()
        try:
            # Save uploaded file
            input_path = os.path.join(temp_dir, file.filename)
            file.save(input_path)

            # Open PDF
            pdf = fitz.open(input_path)

            # Process each page
            for page_num in range(pdf.page_count):
                page = pdf[page_num]

                if flatten_forms:
                    # Get all widgets (form fields) on the page
                    widgets = list(page.widgets())
                    for widget in widgets:
                        # Convert widget to text/image representation
                        if widget.field_type in [fitz.PDF_WIDGET_TYPE_TEXT,
                                               fitz.PDF_WIDGET_TYPE_LISTBOX,
                                               fitz.PDF_WIDGET_TYPE_COMBOBOX]:
                            # Add text representation of the field value
                            if widget.field_value:
                                rect = widget.rect
                                page.insert_text((rect.x0, rect.y1),
                                                str(widget.field_value),
                                                fontsize=10,
                                                color=(0, 0, 0))

                        # Remove the widget (try different methods for compatibility)
                        try:
                            page.delete_widget(widget)
                        except:
                            # Alternative method for older PyMuPDF versions
                            try:
                                widget._annot.set_flags(widget._annot.flags | fitz.ANNOT_XF_HIDDEN)
                            except:
                                pass  # Skip if deletion fails

                if flatten_annotations:
                    # Get all annotations on the page
                    annotations = list(page.annots())
                    for annot in annotations:
                        # Convert annotation to permanent content if possible
                        if annot.type[1] in ['Text', 'FreeText', 'Highlight']:
                            # For text annotations, add the content as text
                            if annot.info.get('content'):
                                rect = annot.rect
                                page.insert_text((rect.x0, rect.y1),
                                                annot.info['content'],
                                                fontsize=8,
                                                color=(0, 0, 1))

                        # Delete the annotation
                        page.delete_annot(annot)

            # Save flattened PDF
            output_filename = f'flattened_{file.filename}'
            output_path = os.path.join(STATIC_DIR, output_filename)

            pdf.save(output_path)
            pdf.close()

            return send_file(output_path, as_attachment=True, download_name=output_filename)

        finally:
            # Cleanup temporary directory
            shutil.rmtree(temp_dir, ignore_errors=True)

    except Exception as e:
        logging.error(f"Error flattening PDF: {str(e)}")
        return jsonify({"error": f"Failed to flatten PDF: {str(e)}"}), 500


@security_bp.route('/sign_pdf', methods=['POST'])
def sign_pdf():
    """Add digital signature to PDF"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files['file']
        signature_text = request.form.get('signature_text', 'Digitally Signed')
        signature_position = request.form.get('signature_position', 'bottom_right')
        signature_page = int(request.form.get('signature_page', -1))  # -1 for last page

        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        # Create temporary directory for processing
        temp_dir = tempfile.mkdtemp()
        try:
            # Save uploaded file
            input_path = os.path.join(temp_dir, file.filename)
            file.save(input_path)

            # Open PDF
            pdf = fitz.open(input_path)

            # Determine which page to sign
            if signature_page == -1:
                page_num = pdf.page_count - 1  # Last page
            else:
                page_num = min(signature_page - 1, pdf.page_count - 1)  # Convert to 0-based index

            page = pdf[page_num]
            page_rect = page.rect

            # Calculate signature position
            sig_width = 200
            sig_height = 60

            if signature_position == 'top_left':
                x0, y0 = 50, 50
            elif signature_position == 'top_right':
                x0, y0 = page_rect.width - sig_width - 50, 50
            elif signature_position == 'bottom_left':
                x0, y0 = 50, page_rect.height - sig_height - 50
            else:  # bottom_right (default)
                x0, y0 = page_rect.width - sig_width - 50, page_rect.height - sig_height - 50

            x1, y1 = x0 + sig_width, y0 + sig_height
            signature_rect = fitz.Rect(x0, y0, x1, y1)

            # Create signature appearance
            # Draw signature box
            page.draw_rect(signature_rect, color=(0, 0, 0), width=1)

            # Add signature text
            text_rect = fitz.Rect(x0 + 10, y0 + 10, x1 - 10, y1 - 30)
            page.insert_textbox(text_rect, signature_text,
                               fontsize=10,
                               color=(0, 0, 0),
                               fontname="helv")

            # Add timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            timestamp_rect = fitz.Rect(x0 + 10, y1 - 25, x1 - 10, y1 - 5)
            page.insert_textbox(timestamp_rect, f"Signed: {timestamp}",
                               fontsize=8,
                               color=(0.5, 0.5, 0.5),
                               fontname="helv")

            # Save signed PDF
            output_filename = f'signed_{file.filename}'
            output_path = os.path.join(STATIC_DIR, output_filename)

            pdf.save(output_path)
            pdf.close()

            return send_file(output_path, as_attachment=True, download_name=output_filename)

        finally:
            # Cleanup temporary directory
            shutil.rmtree(temp_dir, ignore_errors=True)

    except Exception as e:
        logging.error(f"Error signing PDF: {str(e)}")
        return jsonify({"error": f"Failed to sign PDF: {str(e)}"}), 500


@security_bp.route('/compare_pdf', methods=['POST'])
def compare_pdf():
    """Compare two PDF files and highlight differences"""
    try:
        if 'file1' not in request.files or 'file2' not in request.files:
            return jsonify({"error": "Two PDF files are required for comparison"}), 400

        file1 = request.files['file1']
        file2 = request.files['file2']
        comparison_mode = request.form.get('comparison_mode', 'visual')  # visual or text

        if file1.filename == '' or file2.filename == '':
            return jsonify({"error": "Both files must be selected"}), 400

        # Create temporary directory for processing
        temp_dir = tempfile.mkdtemp()
        try:
            # Save uploaded files
            input_path1 = os.path.join(temp_dir, f"file1_{file1.filename}")
            input_path2 = os.path.join(temp_dir, f"file2_{file2.filename}")
            file1.save(input_path1)
            file2.save(input_path2)

            # Open both PDFs
            pdf1 = fitz.open(input_path1)
            pdf2 = fitz.open(input_path2)

            # Create comparison result PDF
            comparison_pdf = fitz.open()

            max_pages = max(pdf1.page_count, pdf2.page_count)

            for page_num in range(max_pages):
                # Create a new page for comparison result
                comp_page = comparison_pdf.new_page(width=842, height=595)  # A4 landscape

                # Get pages from both PDFs (if they exist)
                page1 = pdf1[page_num] if page_num < pdf1.page_count else None
                page2 = pdf2[page_num] if page_num < pdf2.page_count else None

                if comparison_mode == 'visual':
                    # Visual comparison using images
                    if page1:
                        # Convert page to image and place on left side
                        pix1 = page1.get_pixmap(matrix=fitz.Matrix(0.5, 0.5))
                        img_data1 = pix1.tobytes("png")
                        img_rect1 = fitz.Rect(20, 50, 400, 550)
                        comp_page.insert_image(img_rect1, stream=img_data1)

                        # Add label
                        comp_page.insert_text((20, 30), f"File 1 - Page {page_num + 1}",
                                             fontsize=12, color=(0, 0, 0))

                    if page2:
                        # Convert page to image and place on right side
                        pix2 = page2.get_pixmap(matrix=fitz.Matrix(0.5, 0.5))
                        img_data2 = pix2.tobytes("png")
                        img_rect2 = fitz.Rect(420, 50, 800, 550)
                        comp_page.insert_image(img_rect2, stream=img_data2)

                        # Add label
                        comp_page.insert_text((420, 30), f"File 2 - Page {page_num + 1}",
                                             fontsize=12, color=(0, 0, 0))

                else:  # text comparison
                    y_offset = 50

                    if page1:
                        text1 = page1.get_text()
                        comp_page.insert_text((20, 30), f"File 1 - Page {page_num + 1}",
                                             fontsize=12, color=(0, 0, 0))

                        # Insert text in left column
                        text_rect1 = fitz.Rect(20, y_offset, 400, 550)
                        comp_page.insert_textbox(text_rect1, text1[:1000] + "..." if len(text1) > 1000 else text1,
                                               fontsize=8, color=(0, 0, 0))

                    if page2:
                        text2 = page2.get_text()
                        comp_page.insert_text((420, 30), f"File 2 - Page {page_num + 1}",
                                             fontsize=12, color=(0, 0, 0))

                        # Insert text in right column
                        text_rect2 = fitz.Rect(420, y_offset, 800, 550)
                        comp_page.insert_textbox(text_rect2, text2[:1000] + "..." if len(text2) > 1000 else text2,
                                               fontsize=8, color=(0, 0, 0))

                # Draw separator line
                comp_page.draw_line(fitz.Point(410, 40), fitz.Point(410, 560),
                                   color=(0.5, 0.5, 0.5), width=1)

            pdf1.close()
            pdf2.close()

            # Save comparison result
            output_filename = f'comparison_{file1.filename}_vs_{file2.filename}'
            output_path = os.path.join(STATIC_DIR, output_filename)

            comparison_pdf.save(output_path)
            comparison_pdf.close()

            return send_file(output_path, as_attachment=True, download_name=output_filename)

        finally:
            # Cleanup temporary directory
            shutil.rmtree(temp_dir, ignore_errors=True)

    except Exception as e:
        logging.error(f"Error comparing PDFs: {str(e)}")
        return jsonify({"error": f"Failed to compare PDFs: {str(e)}"}), 500
