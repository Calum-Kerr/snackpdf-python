"""
Ghostscript Usage Examples for Remote Agents
Shows how to use the centralized ghostscript_utils module
"""

from .ghostscript_utils import GhostscriptUtils, get_ghostscript_utils
import os
import tempfile

def example_compress_pdf():
    """Example: Compress a PDF file"""
    with GhostscriptUtils() as gs:
        input_pdf = "input.pdf"
        output_pdf = "compressed.pdf"
        
        # Compress with different quality levels
        success, error = gs.compress_pdf(input_pdf, output_pdf, quality='medium')
        
        if success:
            print(f"✅ PDF compressed successfully: {output_pdf}")
        else:
            print(f"❌ Compression failed: {error}")

def example_merge_pdfs():
    """Example: Merge multiple PDFs"""
    with GhostscriptUtils() as gs:
        input_files = ["file1.pdf", "file2.pdf", "file3.pdf"]
        output_file = "merged.pdf"
        
        success, error = gs.merge_pdfs(input_files, output_file)
        
        if success:
            print(f"✅ PDFs merged successfully: {output_file}")
        else:
            print(f"❌ Merge failed: {error}")

def example_split_pdf():
    """Example: Split PDF into pages"""
    with GhostscriptUtils() as gs:
        input_pdf = "document.pdf"
        output_dir = "split_pages"
        
        # Split pages 1-5
        page_files = gs.split_pdf_pages(input_pdf, output_dir, start_page=1, end_page=5)
        
        print(f"✅ Split into {len(page_files)} pages")
        for page_file in page_files:
            print(f"  - {page_file}")

def example_pdf_to_images():
    """Example: Convert PDF to images"""
    with GhostscriptUtils() as gs:
        input_pdf = "document.pdf"
        output_dir = "images"
        
        # Convert to JPEG at 300 DPI
        success, error = gs.pdf_to_images(input_pdf, output_dir, format='jpeg', dpi=300)
        
        if success:
            print(f"✅ PDF converted to images in: {output_dir}")
        else:
            print(f"❌ Conversion failed: {error}")

def example_rotate_pdf():
    """Example: Rotate PDF pages"""
    with GhostscriptUtils() as gs:
        input_pdf = "document.pdf"
        output_pdf = "rotated.pdf"
        
        # Rotate 90 degrees clockwise
        success, error = gs.rotate_pdf(input_pdf, output_pdf, rotation=90)
        
        if success:
            print(f"✅ PDF rotated successfully: {output_pdf}")
        else:
            print(f"❌ Rotation failed: {error}")

def example_get_page_count():
    """Example: Get page count"""
    with GhostscriptUtils() as gs:
        input_pdf = "document.pdf"
        page_count = gs.get_page_count(input_pdf)
        print(f"📄 Document has {page_count} pages")

# Flask route examples for remote agents
def flask_route_example_compress():
    """Example Flask route for PDF compression"""
    from flask import request, send_file, jsonify
    import tempfile
    import os
    
    # This would be in your Flask app
    # @app.route('/api/compress', methods=['POST'])
    def compress_pdf_route():
        try:
            # Get uploaded file
            if 'file' not in request.files:
                return jsonify({'error': 'No file uploaded'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            # Get quality setting
            quality = request.form.get('quality', 'medium')
            
            # Create temporary files
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_input:
                file.save(temp_input.name)
                input_path = temp_input.name
            
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_output:
                output_path = temp_output.name
            
            # Compress using Ghostscript
            with GhostscriptUtils() as gs:
                success, error = gs.compress_pdf(input_path, output_path, quality=quality)
                
                if success:
                    # Clean up input file
                    os.unlink(input_path)
                    
                    # Return compressed file
                    return send_file(
                        output_path,
                        as_attachment=True,
                        download_name=f"compressed_{file.filename}",
                        mimetype='application/pdf'
                    )
                else:
                    # Clean up files
                    os.unlink(input_path)
                    os.unlink(output_path)
                    return jsonify({'error': f'Compression failed: {error}'}), 500
                    
        except Exception as e:
            return jsonify({'error': f'Server error: {str(e)}'}), 500

def flask_route_example_merge():
    """Example Flask route for PDF merging"""
    from flask import request, send_file, jsonify
    import tempfile
    import os
    
    # @app.route('/api/merge', methods=['POST'])
    def merge_pdfs_route():
        try:
            # Get uploaded files
            files = request.files.getlist('files')
            if len(files) < 2:
                return jsonify({'error': 'At least 2 files required for merging'}), 400
            
            # Save uploaded files temporarily
            temp_files = []
            for file in files:
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                    file.save(temp_file.name)
                    temp_files.append(temp_file.name)
            
            # Create output file
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_output:
                output_path = temp_output.name
            
            # Merge using Ghostscript
            with GhostscriptUtils() as gs:
                success, error = gs.merge_pdfs(temp_files, output_path)
                
                # Clean up input files
                for temp_file in temp_files:
                    os.unlink(temp_file)
                
                if success:
                    return send_file(
                        output_path,
                        as_attachment=True,
                        download_name="merged.pdf",
                        mimetype='application/pdf'
                    )
                else:
                    os.unlink(output_path)
                    return jsonify({'error': f'Merge failed: {error}'}), 500
                    
        except Exception as e:
            return jsonify({'error': f'Server error: {str(e)}'}), 500

# Common utility functions for all agents
def validate_pdf_file(file):
    """Validate uploaded PDF file"""
    if not file or file.filename == '':
        return False, "No file selected"
    
    if not file.filename.lower().endswith('.pdf'):
        return False, "File must be a PDF"
    
    # Check file size (e.g., max 50MB)
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)     # Reset to beginning
    
    if size > 50 * 1024 * 1024:  # 50MB
        return False, "File too large (max 50MB)"
    
    return True, None

def create_temp_file(suffix='.pdf'):
    """Create a temporary file"""
    return tempfile.NamedTemporaryFile(suffix=suffix, delete=False)

def cleanup_temp_files(file_paths):
    """Clean up temporary files"""
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Warning: Failed to cleanup {file_path}: {e}")

# Error handling decorator
def handle_ghostscript_errors(func):
    """Decorator to handle common Ghostscript errors"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_msg = str(e)
            if "Ghostscript not found" in error_msg:
                return False, "Ghostscript is not properly installed"
            elif "timeout" in error_msg.lower():
                return False, "Operation timed out - file may be too large"
            elif "permission" in error_msg.lower():
                return False, "Permission denied - check file access"
            else:
                return False, f"Ghostscript error: {error_msg}"
    return wrapper

if __name__ == "__main__":
    print("Ghostscript Examples - Run individual functions to test")
    print("Available examples:")
    print("- example_compress_pdf()")
    print("- example_merge_pdfs()")
    print("- example_split_pdf()")
    print("- example_pdf_to_images()")
    print("- example_rotate_pdf()")
    print("- example_get_page_count()")
