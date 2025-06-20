from flask import Blueprint, request, send_file, jsonify
import fitz  # PyMuPDF
import os
import logging
import shutil
import tempfile
import re
from PIL import Image

edit_content_bp = Blueprint('edit_content', __name__)

STATIC_DIR = os.path.join(os.getcwd(), 'pdf_to_image', 'static')

# Ensure the static directory exists
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

def get_pages_to_edit(pages_option, start_page, end_page, specific_pages, total_pages):
    """Determine which pages to edit based on user selection"""
    if pages_option == 'all':
        return list(range(total_pages))
    elif pages_option == 'current':
        return [0]  # Default to first page for current
    elif pages_option == 'range' and start_page and end_page:
        start = max(0, int(start_page) - 1)
        end = min(total_pages, int(end_page))
        return list(range(start, end))
    elif pages_option == 'specific' and specific_pages:
        pages = []
        for part in specific_pages.split(','):
            part = part.strip()
            if '-' in part:
                start, end = map(int, part.split('-'))
                pages.extend(range(start - 1, min(end, total_pages)))
            else:
                page_num = int(part) - 1
                if 0 <= page_num < total_pages:
                    pages.append(page_num)
        return sorted(list(set(pages)))
    else:
        return list(range(total_pages))

def perform_text_replacement(page, find_text, replace_text, case_sensitive=True):
    """Perform text replacement on a PDF page"""
    try:
        # Get all text instances
        text_instances = page.search_for(find_text)
        
        if not text_instances:
            return False
        
        # Replace text instances
        for inst in text_instances:
            # Get the text block containing this instance
            blocks = page.get_text("dict")
            
            # Find and replace the text
            # Note: This is a simplified approach - full text editing is complex
            page.add_redact_annot(inst, replace_text)
        
        # Apply redactions (this replaces the text)
        page.apply_redactions()
        return True
        
    except Exception as e:
        logging.error(f"Error in text replacement: {e}")
        return False

def add_annotation(page, annotation_type, position=None):
    """Add annotation to PDF page"""
    try:
        rect = page.rect
        
        # Default position (center of page)
        if not position:
            position = fitz.Rect(rect.width * 0.25, rect.height * 0.25, 
                               rect.width * 0.75, rect.height * 0.75)
        
        if annotation_type == 'highlight':
            # Add highlight annotation
            highlight = page.add_highlight_annot(position)
            highlight.set_colors(stroke=(1, 1, 0))  # Yellow
            highlight.update()
            
        elif annotation_type == 'note':
            # Add text annotation (sticky note)
            note = page.add_text_annot(position.tl, "Note")
            note.set_info(content="Click to edit this note")
            note.update()
            
        elif annotation_type == 'comment':
            # Add free text annotation
            comment = page.add_freetext_annot(position, "Comment", fontsize=12)
            comment.update()
            
        elif annotation_type == 'arrow':
            # Add line annotation with arrow
            start_point = position.tl
            end_point = position.br
            arrow = page.add_line_annot(start_point, end_point)
            arrow.set_line_ends(fitz.PDF_ANNOT_LE_NONE, fitz.PDF_ANNOT_LE_CLOSED_ARROW)
            arrow.update()
            
        elif annotation_type == 'rectangle':
            # Add rectangle annotation
            rect_annot = page.add_rect_annot(position)
            rect_annot.set_colors(stroke=(1, 0, 0))  # Red border
            rect_annot.update()
        
        return True
        
    except Exception as e:
        logging.error(f"Error adding annotation: {e}")
        return False

@edit_content_bp.route('/edit_content', methods=['POST'])
def edit_content():
    try:
        # Get form data
        file = request.files['file']
        edit_mode = request.form.get('edit_mode', 'interactive')
        find_text = request.form.get('find_text', '')
        replace_text = request.form.get('replace_text', '')
        replacement_image = request.files.get('replacement_image')
        annotation_type = request.form.get('annotation_type', 'highlight')
        pages_to_edit = request.form.get('pages_to_edit', 'all')
        start_page = request.form.get('start_page')
        end_page = request.form.get('end_page')
        specific_pages = request.form.get('specific_pages', '')
        preserve_formatting = request.form.get('preserve_formatting', 'yes')
        font_matching = request.form.get('font_matching', 'auto')
        quality_level = request.form.get('quality_level', 'high')
        
        output_dir = os.path.join(STATIC_DIR, 'edit_content')
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir, exist_ok=True)

        # Open PDF
        pdf = fitz.open(stream=file.read(), filetype='pdf')
        total_pages = pdf.page_count
        
        # Determine which pages to edit
        pages_to_process = get_pages_to_edit(pages_to_edit, start_page, end_page, specific_pages, total_pages)
        
        changes_made = False
        
        for page_index in pages_to_process:
            if page_index >= total_pages:
                continue
                
            page = pdf[page_index]
            
            if edit_mode == 'text_replacement' and find_text and replace_text:
                if perform_text_replacement(page, find_text, replace_text):
                    changes_made = True
                    
            elif edit_mode == 'image_replacement' and replacement_image:
                # Basic image replacement - replace first image found
                try:
                    image_list = page.get_images()
                    if image_list:
                        # Get first image
                        img_index = image_list[0][0]
                        img_rect = page.get_image_bbox(image_list[0])
                        
                        # Remove old image and insert new one
                        page.delete_image(img_index)
                        
                        # Save replacement image temporarily
                        img_path = os.path.join(output_dir, 'temp_replacement.png')
                        replacement_image.save(img_path)
                        
                        # Insert new image
                        page.insert_image(img_rect, filename=img_path)
                        changes_made = True
                        
                except Exception as e:
                    logging.error(f"Error replacing image: {e}")
                    
            elif edit_mode == 'annotation':
                if add_annotation(page, annotation_type):
                    changes_made = True
                    
            elif edit_mode == 'interactive':
                # For interactive mode, we'll add a sample annotation to show it's working
                # In a real implementation, this would involve a more complex UI
                if add_annotation(page, 'note'):
                    changes_made = True

        if not changes_made:
            return jsonify({"error": "No changes were made to the PDF"}), 400

        # Save the edited PDF
        output_path = os.path.join(output_dir, f'edited_{file.filename}')
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
        logging.error(f"Error editing PDF content: {e}")
        return jsonify({"error": f"Failed to edit PDF content: {str(e)}"}), 500
