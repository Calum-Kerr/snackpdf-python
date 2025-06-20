from flask import Blueprint, request, send_file, jsonify
import fitz  # PyMuPDF
import os
import logging
import shutil
import tempfile
import re

redact_bp = Blueprint('redact', __name__)

STATIC_DIR = os.path.join(os.getcwd(), 'pdf_to_image', 'static')

# Ensure the static directory exists
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

# Pattern definitions for common sensitive data
PATTERNS = {
    'ssn': r'\b\d{3}-\d{2}-\d{4}\b|\b\d{9}\b',
    'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
    'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b|\(\d{3}\)\s?\d{3}[-.]?\d{4}\b',
    'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
}

# Simple patterns for AI detection (basic pattern matching)
AI_PATTERNS = {
    'names': r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',  # Simple name pattern
    'addresses': r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd)\b',
    'financial': r'\$\d+(?:,\d{3})*(?:\.\d{2})?|\b\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:dollars?|USD)\b',
    'medical': r'\b(?:patient|diagnosis|treatment|medication|prescription|doctor|physician|hospital)\b'
}

def find_text_instances(page, search_text, case_sensitive=True):
    """Find all instances of text on a page"""
    try:
        if case_sensitive:
            return page.search_for(search_text)
        else:
            return page.search_for(search_text, flags=fitz.TEXT_DEHYPHENATE)
    except:
        return []

def find_pattern_instances(page, pattern):
    """Find all instances matching a regex pattern on a page"""
    try:
        text = page.get_text()
        matches = []
        for match in re.finditer(pattern, text, re.IGNORECASE):
            # Find the text rectangles for this match
            search_results = page.search_for(match.group())
            matches.extend(search_results)
        return matches
    except Exception as e:
        logging.error(f"Error finding pattern instances: {e}")
        return []

def apply_redaction_style(page, rect, style, replacement_text="[REDACTED]"):
    """Apply redaction with specified style"""
    try:
        if style == 'black_box':
            # Standard black redaction
            redact_annot = page.add_redact_annot(rect)
            redact_annot.update()
            
        elif style == 'white_box':
            # White box redaction
            redact_annot = page.add_redact_annot(rect, fill=(1, 1, 1))
            redact_annot.update()
            
        elif style == 'strikethrough':
            # Add strikethrough annotation
            strike_annot = page.add_strikeout_annot(rect)
            strike_annot.update()
            
        elif style == 'blur':
            # Simulate blur by adding a semi-transparent overlay
            # Note: True blur would require image processing
            redact_annot = page.add_redact_annot(rect, fill=(0.8, 0.8, 0.8))
            redact_annot.update()
            
        elif style == 'custom_text':
            # Replace with custom text
            redact_annot = page.add_redact_annot(rect, text=replacement_text)
            redact_annot.update()
        
        return True
        
    except Exception as e:
        logging.error(f"Error applying redaction style: {e}")
        return False

@redact_bp.route('/redact', methods=['POST'])
def redact_pdf():
    try:
        # Get form data
        file = request.files['file']
        redaction_method = request.form.get('redaction_method', 'manual')
        search_terms = request.form.get('search_terms', '')
        pattern_type = request.form.get('pattern_type', 'ssn')
        redaction_style = request.form.get('redaction_style', 'black_box')
        replacement_text = request.form.get('replacement_text', '[REDACTED]')
        case_sensitive = request.form.get('case_sensitive', 'no') == 'yes'
        
        # AI detection options
        detect_names = request.form.get('detect_names') == 'yes'
        detect_addresses = request.form.get('detect_addresses') == 'yes'
        detect_financial = request.form.get('detect_financial') == 'yes'
        detect_medical = request.form.get('detect_medical') == 'yes'
        
        output_dir = os.path.join(STATIC_DIR, 'redact')
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir, exist_ok=True)

        # Open PDF
        pdf = fitz.open(stream=file.read(), filetype='pdf')
        
        redactions_made = False
        
        for page_num in range(pdf.page_count):
            page = pdf[page_num]
            redaction_rects = []
            
            if redaction_method == 'text_search' and search_terms:
                # Search for specific terms
                terms = [term.strip() for term in search_terms.split(',')]
                for term in terms:
                    if term:
                        instances = find_text_instances(page, term, case_sensitive)
                        redaction_rects.extend(instances)
                        
            elif redaction_method == 'pattern_matching':
                # Use predefined patterns
                if pattern_type in PATTERNS:
                    pattern = PATTERNS[pattern_type]
                    instances = find_pattern_instances(page, pattern)
                    redaction_rects.extend(instances)
                    
            elif redaction_method == 'ai_detection':
                # Use AI patterns (basic pattern matching)
                if detect_names:
                    instances = find_pattern_instances(page, AI_PATTERNS['names'])
                    redaction_rects.extend(instances)
                if detect_addresses:
                    instances = find_pattern_instances(page, AI_PATTERNS['addresses'])
                    redaction_rects.extend(instances)
                if detect_financial:
                    instances = find_pattern_instances(page, AI_PATTERNS['financial'])
                    redaction_rects.extend(instances)
                if detect_medical:
                    instances = find_pattern_instances(page, AI_PATTERNS['medical'])
                    redaction_rects.extend(instances)
                    
            elif redaction_method == 'manual':
                # For manual redaction, we'll create a sample redaction in the center
                # In a real implementation, this would be handled by a UI
                rect = page.rect
                sample_rect = fitz.Rect(
                    rect.width * 0.25, rect.height * 0.4,
                    rect.width * 0.75, rect.height * 0.6
                )
                redaction_rects.append(sample_rect)
            
            # Apply redactions
            for rect in redaction_rects:
                if apply_redaction_style(page, rect, redaction_style, replacement_text):
                    redactions_made = True
            
            # Apply all redactions on this page
            if redaction_rects:
                page.apply_redactions()

        if not redactions_made:
            return jsonify({"error": "No content was found to redact"}), 400

        # Save the redacted PDF
        output_path = os.path.join(output_dir, f'redacted_{file.filename}')
        pdf.save(output_path)
        pdf.close()

        return send_file(output_path, as_attachment=True)

    except Exception as e:
        logging.error(f"Error redacting PDF: {e}")
        return jsonify({"error": f"Failed to redact PDF: {str(e)}"}), 500

@redact_bp.route('/redact_preview', methods=['POST'])
def redact_preview():
    """Preview redactions before applying them permanently"""
    try:
        # This would be used for preview functionality
        # For now, return a simple response
        return jsonify({"message": "Preview functionality - shows redaction areas before final processing"}), 200
        
    except Exception as e:
        logging.error(f"Error in redact preview: {e}")
        return jsonify({"error": f"Failed to generate preview: {str(e)}"}), 500
