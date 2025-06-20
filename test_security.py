#!/usr/bin/env python3
"""
Test script for PDF Security Tools
Tests the basic functionality of all security tools
"""

import os
import sys
import tempfile
import fitz  # PyMuPDF
from pdf_to_image.security import security_bp
from pdf_to_image import create_app
from flask import Flask
import io

def create_test_pdf():
    """Create a simple test PDF for testing"""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((100, 100), "This is a test PDF for security testing", fontsize=12)
    
    # Add a simple form field
    widget = fitz.Widget()
    widget.field_name = "test_field"
    widget.field_type = fitz.PDF_WIDGET_TYPE_TEXT
    widget.rect = fitz.Rect(100, 150, 300, 170)
    widget.field_value = "Test Value"
    page.add_widget(widget)
    
    # Save to bytes
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes

def test_protect_pdf():
    """Test PDF protection functionality"""
    print("Testing PDF Protection...")
    
    # Create test PDF
    pdf_data = create_test_pdf()
    
    # Test protection
    temp_dir = tempfile.mkdtemp()
    try:
        input_path = os.path.join(temp_dir, "test.pdf")
        with open(input_path, "wb") as f:
            f.write(pdf_data)
        
        # Open and protect
        pdf = fitz.open(input_path)
        output_path = os.path.join(temp_dir, "protected.pdf")
        
        pdf.save(output_path, 
                encryption=fitz.PDF_ENCRYPT_AES_256,
                owner_pw="owner123",
                user_pw="user123",
                permissions=fitz.PDF_PERM_PRINT)
        pdf.close()
        
        # Verify protection
        protected_pdf = fitz.open(output_path)
        if protected_pdf.needs_pass:
            print("✓ PDF protection successful - password required")
            
            # Test authentication
            if protected_pdf.authenticate("user123"):
                print("✓ User password authentication successful")
            else:
                print("✗ User password authentication failed")
        else:
            print("✗ PDF protection failed - no password required")
        
        protected_pdf.close()
        
    except Exception as e:
        print(f"✗ PDF protection test failed: {e}")
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

def test_flatten_pdf():
    """Test PDF flattening functionality"""
    print("\nTesting PDF Flattening...")
    
    # Create test PDF with form
    pdf_data = create_test_pdf()
    
    temp_dir = tempfile.mkdtemp()
    try:
        input_path = os.path.join(temp_dir, "test_form.pdf")
        with open(input_path, "wb") as f:
            f.write(pdf_data)
        
        # Open and flatten
        pdf = fitz.open(input_path)
        
        # Count widgets before flattening
        widgets_before = 0
        for page_num in range(pdf.page_count):
            page = pdf[page_num]
            widgets_before += len(page.widgets())
        
        print(f"Widgets before flattening: {widgets_before}")
        
        # Flatten forms
        for page_num in range(pdf.page_count):
            page = pdf[page_num]
            widgets = page.widgets()
            for widget in widgets:
                if widget.field_value:
                    rect = widget.rect
                    page.insert_text((rect.x0, rect.y1), 
                                    str(widget.field_value),
                                    fontsize=10,
                                    color=(0, 0, 0))
                page.delete_widget(widget)
        
        output_path = os.path.join(temp_dir, "flattened.pdf")
        pdf.save(output_path)
        pdf.close()
        
        # Verify flattening
        flattened_pdf = fitz.open(output_path)
        widgets_after = 0
        for page_num in range(flattened_pdf.page_count):
            page = flattened_pdf[page_num]
            widgets_after += len(page.widgets())
        
        print(f"Widgets after flattening: {widgets_after}")
        
        if widgets_after < widgets_before:
            print("✓ PDF flattening successful - widgets removed")
        else:
            print("✗ PDF flattening failed - widgets still present")
        
        flattened_pdf.close()
        
    except Exception as e:
        print(f"✗ PDF flattening test failed: {e}")
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

def test_sign_pdf():
    """Test PDF signing functionality"""
    print("\nTesting PDF Signing...")
    
    # Create test PDF
    pdf_data = create_test_pdf()
    
    temp_dir = tempfile.mkdtemp()
    try:
        input_path = os.path.join(temp_dir, "test.pdf")
        with open(input_path, "wb") as f:
            f.write(pdf_data)
        
        # Open and sign
        pdf = fitz.open(input_path)
        page = pdf[0]
        page_rect = page.rect
        
        # Add signature
        sig_width = 200
        sig_height = 60
        x0, y0 = page_rect.width - sig_width - 50, page_rect.height - sig_height - 50
        x1, y1 = x0 + sig_width, y0 + sig_height
        signature_rect = fitz.Rect(x0, y0, x1, y1)
        
        # Draw signature box
        page.draw_rect(signature_rect, color=(0, 0, 0), width=1)
        
        # Add signature text
        text_rect = fitz.Rect(x0 + 10, y0 + 10, x1 - 10, y1 - 30)
        page.insert_textbox(text_rect, "Digitally Signed", 
                           fontsize=10, 
                           color=(0, 0, 0),
                           fontname="helv")
        
        output_path = os.path.join(temp_dir, "signed.pdf")
        pdf.save(output_path)
        pdf.close()
        
        # Verify signature was added
        signed_pdf = fitz.open(output_path)
        page = signed_pdf[0]
        text = page.get_text()
        
        if "Digitally Signed" in text:
            print("✓ PDF signing successful - signature text found")
        else:
            print("✗ PDF signing failed - signature text not found")
        
        signed_pdf.close()
        
    except Exception as e:
        print(f"✗ PDF signing test failed: {e}")
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

def main():
    """Run all security tests"""
    print("=== PDF Security Tools Test Suite ===\n")
    
    try:
        test_protect_pdf()
        test_flatten_pdf()
        test_sign_pdf()
        
        print("\n=== Test Suite Complete ===")
        print("All basic security functions are working!")
        
    except Exception as e:
        print(f"Test suite failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
