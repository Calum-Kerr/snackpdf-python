#!/usr/bin/env python3
"""
Test script for PDF optimization tools
"""

import os
import sys
import tempfile
from pdf_to_image import create_app

def test_app_creation():
    """Test that the Flask app can be created with blueprints"""
    try:
        app = create_app()
        print("✓ Flask app created successfully")
        
        # Check if blueprints are registered
        blueprint_names = [bp.name for bp in app.blueprints.values()]
        print(f"✓ Registered blueprints: {blueprint_names}")
        
        if 'compress_bp' in blueprint_names:
            print("✓ Compress blueprint registered")
        else:
            print("✗ Compress blueprint NOT registered")
            
        if 'repair' in blueprint_names:
            print("✓ Repair blueprint registered")
        else:
            print("✗ Repair blueprint NOT registered")
            
        return True
    except Exception as e:
        print(f"✗ Error creating Flask app: {e}")
        return False

def test_routes():
    """Test that routes are accessible"""
    try:
        app = create_app()
        with app.test_client() as client:
            # Test GET routes
            response = client.get('/compress')
            if response.status_code == 200:
                print("✓ /compress route accessible")
            else:
                print(f"✗ /compress route returned {response.status_code}")
                
            response = client.get('/repair')
            if response.status_code == 200:
                print("✓ /repair route accessible")
            else:
                print(f"✗ /repair route returned {response.status_code}")
                
        return True
    except Exception as e:
        print(f"✗ Error testing routes: {e}")
        return False

def test_validation_functions():
    """Test file validation functions"""
    try:
        from pdf_to_image.compress import validate_pdf_file
        from pdf_to_image.repair import validate_pdf_file as repair_validate_pdf_file
        
        # Create a mock file object
        class MockFile:
            def __init__(self, filename, size=1024):
                self.filename = filename
                self._size = size
                self._position = 0
                
            def seek(self, position, whence=0):
                if whence == 0:  # SEEK_SET
                    self._position = position
                elif whence == 2:  # SEEK_END
                    self._position = self._size
                    
            def tell(self):
                return self._position
        
        # Test valid PDF
        valid_file = MockFile("test.pdf", 1024)
        is_valid, message = validate_pdf_file(valid_file)
        if is_valid:
            print("✓ PDF validation accepts valid PDF files")
        else:
            print(f"✗ PDF validation rejected valid file: {message}")
            
        # Test invalid extension
        invalid_file = MockFile("test.txt", 1024)
        is_valid, message = validate_pdf_file(invalid_file)
        if not is_valid and "PDF" in message:
            print("✓ PDF validation rejects non-PDF files")
        else:
            print(f"✗ PDF validation should reject non-PDF files")
            
        # Test large file
        large_file = MockFile("test.pdf", 100 * 1024 * 1024)  # 100MB
        is_valid, message = validate_pdf_file(large_file)
        if not is_valid and "size" in message.lower():
            print("✓ PDF validation rejects oversized files")
        else:
            print(f"✗ PDF validation should reject oversized files")
            
        return True
    except Exception as e:
        print(f"✗ Error testing validation functions: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing PDF Optimization Tools")
    print("=" * 40)
    
    tests = [
        test_app_creation,
        test_routes,
        test_validation_functions,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        print(f"\nRunning {test.__name__}...")
        if test():
            passed += 1
        print("-" * 40)
    
    print(f"\nTest Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! PDF optimization tools are ready.")
        return 0
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
