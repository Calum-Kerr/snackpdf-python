from flask import Blueprint, request, send_file, jsonify
import os
import tempfile
import logging
import uuid
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4, A3, A5, legal
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from bs4 import BeautifulSoup
import io

html_to_pdf_bp = Blueprint('html_to_pdf', __name__)

STATIC_DIR = os.path.join(os.getcwd(), 'pdf_to_image', 'static')

# Ensure the static directory exists
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Supported file formats
HTML_FORMATS = {'.html', '.htm'}

def validate_file(file, allowed_extensions):
    """Validate uploaded file"""
    if not file or file.filename == '':
        return False, "No file selected"
    
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        return False, f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
    
    # Check file size (max 10MB for HTML)
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > 10 * 1024 * 1024:  # 10MB
        return False, "File too large. Maximum size is 10MB"
    
    return True, "Valid file"

def convert_html_to_pdf(html_content, output_path, page_size='A4', orientation='portrait'):
    """Convert HTML content to PDF using ReportLab"""
    try:
        # Parse HTML content
        soup = BeautifulSoup(html_content, 'html.parser')

        # Get page size
        page_sizes = {
            'A4': A4,
            'A3': A3,
            'A5': A5,
            'Letter': letter,
            'Legal': legal
        }

        page_format = page_sizes.get(page_size, A4)
        if orientation == 'landscape':
            page_format = (page_format[1], page_format[0])

        # Create PDF document
        doc = SimpleDocTemplate(output_path, pagesize=page_format)
        styles = getSampleStyleSheet()
        story = []

        # Extract text content and basic formatting
        for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div', 'span']):
            text = element.get_text().strip()
            if text:
                # Determine style based on tag
                if element.name in ['h1', 'h2', 'h3']:
                    style = styles['Heading1']
                elif element.name in ['h4', 'h5', 'h6']:
                    style = styles['Heading2']
                else:
                    style = styles['Normal']

                # Create paragraph
                para = Paragraph(text, style)
                story.append(para)
                story.append(Spacer(1, 12))

        # If no structured content found, use raw text
        if not story:
            text = soup.get_text()
            if text.strip():
                para = Paragraph(text, styles['Normal'])
                story.append(para)

        # Build PDF
        doc.build(story)
        return True, "Conversion successful"

    except Exception as e:
        logging.error(f"Error converting HTML to PDF: {str(e)}")
        return False, f"Conversion failed: {str(e)}"

def validate_html_content(html_content):
    """Basic validation and sanitization of HTML content"""
    try:
        # Check if content is not empty
        if not html_content.strip():
            return False, "HTML content is empty"
        
        # Add basic HTML structure if missing
        if '<html>' not in html_content.lower():
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Converted Document</title>
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """
        
        return True, html_content
        
    except Exception as e:
        return False, f"HTML validation failed: {str(e)}"

@html_to_pdf_bp.route('/api/html_to_pdf', methods=['POST'])
def html_to_pdf():
    """Convert HTML file to PDF"""
    try:
        # Check if file or HTML content is provided
        file = request.files.get('file')
        html_content = request.form.get('html_content', '')
        
        if file:
            # Validate file
            is_valid, message = validate_file(file, HTML_FORMATS)
            if not is_valid:
                return jsonify({"error": message}), 400
            
            # Read HTML content from file
            html_content = file.read().decode('utf-8')
        
        elif html_content:
            # Use provided HTML content
            pass
        else:
            return jsonify({"error": "No HTML file or content provided"}), 400
        
        # Validate HTML content
        is_valid, result = validate_html_content(html_content)
        if not is_valid:
            return jsonify({"error": result}), 400
        
        html_content = result
        
        # Get options
        page_size = request.form.get('page_size', 'A4')
        orientation = request.form.get('orientation', 'portrait')
        
        # Validate options
        valid_page_sizes = ['A4', 'A3', 'A5', 'Letter', 'Legal']
        valid_orientations = ['portrait', 'landscape']
        
        if page_size not in valid_page_sizes:
            page_size = 'A4'
        
        if orientation not in valid_orientations:
            orientation = 'portrait'
        
        # Generate unique filename
        unique_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"converted_html_{timestamp}_{unique_id}.pdf"
        output_path = os.path.join(STATIC_DIR, output_filename)
        
        # Convert to PDF
        success, message = convert_html_to_pdf(html_content, output_path, page_size, orientation)
        
        if not success:
            return jsonify({"error": message}), 500
        
        return send_file(output_path, as_attachment=True, download_name=output_filename)
        
    except Exception as e:
        logging.error(f"Error in html_to_pdf: {str(e)}")
        return jsonify({"error": f"Conversion failed: {str(e)}"}), 500

@html_to_pdf_bp.route('/api/url_to_pdf', methods=['POST'])
def url_to_pdf():
    """Convert URL to PDF"""
    try:
        url = request.form.get('url', '').strip()
        
        if not url:
            return jsonify({"error": "No URL provided"}), 400
        
        # Basic URL validation
        if not (url.startswith('http://') or url.startswith('https://')):
            url = 'https://' + url
        
        # Get options
        page_size = request.form.get('page_size', 'A4')
        orientation = request.form.get('orientation', 'portrait')
        
        # Validate options
        valid_page_sizes = ['A4', 'A3', 'A5', 'Letter', 'Legal']
        valid_orientations = ['portrait', 'landscape']
        
        if page_size not in valid_page_sizes:
            page_size = 'A4'
        
        if orientation not in valid_orientations:
            orientation = 'portrait'
        
        # Generate unique filename
        unique_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"converted_url_{timestamp}_{unique_id}.pdf"
        output_path = os.path.join(STATIC_DIR, output_filename)
        
        try:
            # For URL conversion, we'll use a simple approach
            # In a production environment, you might want to use a headless browser
            import urllib.request

            # Fetch URL content
            with urllib.request.urlopen(url) as response:
                html_content = response.read().decode('utf-8')

            # Convert to PDF
            success, message = convert_html_to_pdf(html_content, output_path, page_size, orientation)

            if not success:
                return jsonify({"error": message}), 500

            return send_file(output_path, as_attachment=True, download_name=output_filename)

        except Exception as e:
            logging.error(f"Error converting URL to PDF: {str(e)}")
            return jsonify({"error": f"Failed to convert URL: {str(e)}"}), 500
        
    except Exception as e:
        logging.error(f"Error in url_to_pdf: {str(e)}")
        return jsonify({"error": f"Conversion failed: {str(e)}"}), 500
