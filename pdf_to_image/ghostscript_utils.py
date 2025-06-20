"""
Centralized Ghostscript Utility Module for SnackPDF
Provides common Ghostscript operations for all remote agents
"""

import subprocess
import os
import tempfile
import shutil
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GhostscriptError(Exception):
    """Custom exception for Ghostscript operations"""
    pass

class GhostscriptUtils:
    """Centralized Ghostscript utility class"""
    
    def __init__(self):
        self.gs_command = self._find_ghostscript()
        self.temp_dir = tempfile.mkdtemp(prefix='snackpdf_')
        
    def _find_ghostscript(self):
        """Find Ghostscript executable"""
        possible_commands = ['gs', 'ghostscript', '/usr/bin/gs']
        
        for cmd in possible_commands:
            try:
                result = subprocess.run([cmd, '--version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    logger.info(f"Found Ghostscript: {cmd} - Version: {result.stdout.strip()}")
                    return cmd
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
                
        raise GhostscriptError("Ghostscript not found. Please ensure it's installed.")
    
    def check_installation(self):
        """Verify Ghostscript is properly installed"""
        try:
            result = subprocess.run([self.gs_command, '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return True, result.stdout.strip()
            else:
                return False, result.stderr
        except Exception as e:
            return False, str(e)
    
    def compress_pdf(self, input_path, output_path, quality='medium'):
        """
        Compress PDF using Ghostscript
        Quality options: 'low', 'medium', 'high', 'maximum'
        """
        quality_settings = {
            'low': '/screen',      # 72 DPI
            'medium': '/ebook',    # 150 DPI  
            'high': '/printer',    # 300 DPI
            'maximum': '/prepress' # 300+ DPI
        }
        
        if quality not in quality_settings:
            quality = 'medium'
            
        cmd = [
            self.gs_command,
            '-sDEVICE=pdfwrite',
            '-dCompatibilityLevel=1.4',
            f'-dPDFSETTINGS={quality_settings[quality]}',
            '-dNOPAUSE',
            '-dQUIET',
            '-dBATCH',
            f'-sOutputFile={output_path}',
            input_path
        ]
        
        return self._run_command(cmd)
    
    def merge_pdfs(self, input_paths, output_path):
        """Merge multiple PDFs into one"""
        cmd = [
            self.gs_command,
            '-sDEVICE=pdfwrite',
            '-dNOPAUSE',
            '-dQUIET',
            '-dBATCH',
            f'-sOutputFile={output_path}'
        ] + input_paths
        
        return self._run_command(cmd)
    
    def split_pdf_pages(self, input_path, output_dir, start_page=1, end_page=None):
        """Split PDF into individual pages"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Get total pages first
        total_pages = self.get_page_count(input_path)
        if end_page is None:
            end_page = total_pages
            
        output_files = []
        for page in range(start_page, min(end_page + 1, total_pages + 1)):
            output_file = os.path.join(output_dir, f'page_{page:03d}.pdf')
            cmd = [
                self.gs_command,
                '-sDEVICE=pdfwrite',
                '-dNOPAUSE',
                '-dQUIET',
                '-dBATCH',
                f'-dFirstPage={page}',
                f'-dLastPage={page}',
                f'-sOutputFile={output_file}',
                input_path
            ]
            
            success, error = self._run_command(cmd)
            if success:
                output_files.append(output_file)
            else:
                logger.error(f"Failed to extract page {page}: {error}")
                
        return output_files
    
    def pdf_to_images(self, input_path, output_dir, format='jpeg', dpi=150):
        """Convert PDF pages to images"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        device_map = {
            'jpeg': 'jpeg',
            'jpg': 'jpeg', 
            'png': 'png16m',
            'tiff': 'tiff24nc'
        }
        
        device = device_map.get(format.lower(), 'jpeg')
        output_pattern = os.path.join(output_dir, f'page_%03d.{format.lower()}')
        
        cmd = [
            self.gs_command,
            f'-sDEVICE={device}',
            f'-r{dpi}',
            '-dNOPAUSE',
            '-dQUIET',
            '-dBATCH',
            f'-sOutputFile={output_pattern}',
            input_path
        ]
        
        return self._run_command(cmd)
    
    def rotate_pdf(self, input_path, output_path, rotation=90):
        """Rotate PDF pages (90, 180, 270 degrees)"""
        if rotation not in [90, 180, 270]:
            raise GhostscriptError("Rotation must be 90, 180, or 270 degrees")
            
        # Create PostScript rotation command
        ps_rotation = f"<</Rotate {rotation}>> setpagedevice"
        
        cmd = [
            self.gs_command,
            '-sDEVICE=pdfwrite',
            '-dNOPAUSE',
            '-dQUIET',
            '-dBATCH',
            f'-sOutputFile={output_path}',
            '-c', ps_rotation,
            '-f', input_path
        ]
        
        return self._run_command(cmd)
    
    def add_watermark(self, input_path, watermark_path, output_path):
        """Add watermark to PDF"""
        cmd = [
            self.gs_command,
            '-sDEVICE=pdfwrite',
            '-dNOPAUSE',
            '-dQUIET',
            '-dBATCH',
            f'-sOutputFile={output_path}',
            input_path,
            watermark_path
        ]
        
        return self._run_command(cmd)
    
    def get_page_count(self, input_path):
        """Get number of pages in PDF"""
        cmd = [
            self.gs_command,
            '-q',
            '-dNODISPLAY',
            '-c',
            f'({input_path}) (r) file runpdfbegin pdfpagecount = quit'
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return int(result.stdout.strip())
            else:
                logger.error(f"Failed to get page count: {result.stderr}")
                return 0
        except Exception as e:
            logger.error(f"Error getting page count: {e}")
            return 0
    
    def _run_command(self, cmd):
        """Execute Ghostscript command"""
        try:
            logger.info(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                return True, None
            else:
                error_msg = result.stderr or result.stdout
                logger.error(f"Ghostscript error: {error_msg}")
                return False, error_msg
                
        except subprocess.TimeoutExpired:
            error_msg = "Ghostscript operation timed out"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def cleanup(self):
        """Clean up temporary files"""
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        except Exception as e:
            logger.warning(f"Failed to cleanup temp directory: {e}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

# Convenience functions for quick access
def get_ghostscript_utils():
    """Get a GhostscriptUtils instance"""
    return GhostscriptUtils()

def test_ghostscript():
    """Test Ghostscript installation"""
    try:
        with GhostscriptUtils() as gs:
            success, version = gs.check_installation()
            if success:
                print(f"✅ Ghostscript is working! Version: {version}")
                return True
            else:
                print(f"❌ Ghostscript test failed: {version}")
                return False
    except Exception as e:
        print(f"❌ Ghostscript test error: {e}")
        return False

if __name__ == "__main__":
    test_ghostscript()
