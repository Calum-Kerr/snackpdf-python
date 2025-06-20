#!/usr/bin/env python3
"""
Test script for Convert to PDF functionality
"""

import os
import tempfile
from io import BytesIO
from PIL import Image
from pdf_to_image import create_app

def test_jpg_to_pdf():
    """Test JPG to PDF conversion"""
    print("Testing JPG to PDF conversion...")
    
    app = create_app()
    
    with app.test_client() as client:
        # Create a simple test image
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        # Test the conversion
        response = client.post('/api/jpg_to_pdf', data={
            'file': (img_bytes, 'test.jpg'),
            'page_size': 'A4',
            'quality': '95'
        })
        
        print(f"JPG to PDF response status: {response.status_code}")
        if response.status_code == 200:
            print("✓ JPG to PDF conversion successful")
            print(f"Response content type: {response.content_type}")
        else:
            print(f"✗ JPG to PDF conversion failed: {response.get_json()}")

def test_html_to_pdf():
    """Test HTML to PDF conversion"""
    print("\nTesting HTML to PDF conversion...")
    
    app = create_app()
    
    with app.test_client() as client:
        # Create a simple HTML file
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Document</title>
        </head>
        <body>
            <h1>Test HTML to PDF</h1>
            <p>This is a test paragraph.</p>
            <h2>Subheading</h2>
            <p>Another paragraph with some content.</p>
        </body>
        </html>
        """
        
        html_bytes = BytesIO(html_content.encode('utf-8'))
        
        # Test the conversion
        response = client.post('/api/html_to_pdf', data={
            'file': (html_bytes, 'test.html'),
            'page_size': 'A4',
            'orientation': 'portrait'
        })
        
        print(f"HTML to PDF response status: {response.status_code}")
        if response.status_code == 200:
            print("✓ HTML to PDF conversion successful")
            print(f"Response content type: {response.content_type}")
        else:
            print(f"✗ HTML to PDF conversion failed: {response.get_json()}")

def test_word_to_pdf():
    """Test Word to PDF conversion (will fail without actual Word file)"""
    print("\nTesting Word to PDF conversion...")
    
    app = create_app()
    
    with app.test_client() as client:
        # Create a fake Word file (will fail but tests the endpoint)
        fake_docx = BytesIO(b"fake docx content")
        
        response = client.post('/api/word_to_pdf', data={
            'file': (fake_docx, 'test.docx')
        })
        
        print(f"Word to PDF response status: {response.status_code}")
        if response.status_code == 500:
            print("✓ Word to PDF endpoint working (expected failure with fake file)")
        else:
            print(f"Word to PDF response: {response.get_json()}")

if __name__ == "__main__":
    print("Testing Convert to PDF functionality...\n")
    
    try:
        test_jpg_to_pdf()
        test_html_to_pdf()
        test_word_to_pdf()
        print("\n✓ All tests completed!")
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
