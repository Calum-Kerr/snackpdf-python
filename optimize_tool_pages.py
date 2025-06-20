#!/usr/bin/env python3
"""
Script to add optimized SEO meta tags to all tool pages
"""

import os

# Tool page SEO data
TOOL_SEO_DATA = {
    'compress': {
        'title': 'Compress PDF Online Free - Reduce PDF File Size | SnackPDF',
        'description': 'Compress PDF files online for free. Reduce PDF file size without losing quality. Fast, secure, and easy PDF compression tool. No registration required.',
        'keywords': 'compress PDF, reduce PDF size, PDF compressor, shrink PDF, PDF file size reducer, online PDF compression',
        'canonical': 'https://www.snackpdf.com/compress'
    },
    'jpg_to_pdf': {
        'title': 'JPG to PDF Converter - Convert Images to PDF Free | SnackPDF',
        'description': 'Convert JPG, JPEG, PNG images to PDF online for free. Merge multiple images into one PDF. Fast, secure image to PDF converter.',
        'keywords': 'JPG to PDF, image to PDF, JPEG to PDF, PNG to PDF, convert images to PDF, photo to PDF',
        'canonical': 'https://www.snackpdf.com/jpg_to_pdf'
    },
    'merge': {
        'title': 'Merge PDF Files Online Free - Combine PDFs | SnackPDF',
        'description': 'Merge multiple PDF files into one document online for free. Combine PDFs quickly and securely. No software installation required.',
        'keywords': 'merge PDF, combine PDF, join PDF files, PDF merger, unite PDFs, concatenate PDF',
        'canonical': 'https://www.snackpdf.com/merge'
    },
    'split': {
        'title': 'Split PDF Online Free - Extract Pages from PDF | SnackPDF',
        'description': 'Split PDF files online for free. Extract specific pages or split into multiple documents. Fast and secure PDF splitter tool.',
        'keywords': 'split PDF, extract PDF pages, divide PDF, separate PDF pages, PDF splitter, break PDF',
        'canonical': 'https://www.snackpdf.com/split'
    },
    'pdf_to_jpg': {
        'title': 'PDF to JPG Converter - Convert PDF to Images Free | SnackPDF',
        'description': 'Convert PDF to JPG, PNG images online for free. Extract images from PDF documents. High-quality PDF to image conversion.',
        'keywords': 'PDF to JPG, PDF to image, PDF to PNG, convert PDF to pictures, extract images from PDF',
        'canonical': 'https://www.snackpdf.com/pdf_to_jpg'
    },
    'word_to_pdf': {
        'title': 'Word to PDF Converter - Convert DOC to PDF Free | SnackPDF',
        'description': 'Convert Word documents (DOC, DOCX) to PDF online for free. Preserve formatting and layout. Fast Word to PDF conversion.',
        'keywords': 'Word to PDF, DOC to PDF, DOCX to PDF, convert Word to PDF, document to PDF',
        'canonical': 'https://www.snackpdf.com/word_to_pdf'
    },
    'word': {
        'title': 'PDF to Word Converter - Convert PDF to DOC Free | SnackPDF',
        'description': 'Convert PDF to Word (DOC, DOCX) online for free. Edit PDF content in Word. Accurate PDF to Word conversion with preserved formatting.',
        'keywords': 'PDF to Word, PDF to DOC, PDF to DOCX, convert PDF to Word, edit PDF in Word',
        'canonical': 'https://www.snackpdf.com/word'
    },
    'unlock': {
        'title': 'Unlock PDF Online Free - Remove PDF Password | SnackPDF',
        'description': 'Remove password protection from PDF files online for free. Unlock encrypted PDFs quickly and securely. No software needed.',
        'keywords': 'unlock PDF, remove PDF password, decrypt PDF, PDF password remover, unlock encrypted PDF',
        'canonical': 'https://www.snackpdf.com/unlock'
    },
    'protect': {
        'title': 'Protect PDF with Password - Secure PDF Online Free | SnackPDF',
        'description': 'Add password protection to PDF files online for free. Secure your PDFs with encryption. Easy PDF password protection tool.',
        'keywords': 'protect PDF, PDF password, secure PDF, encrypt PDF, add password to PDF, PDF security',
        'canonical': 'https://www.snackpdf.com/protect'
    },
    'rotate': {
        'title': 'Rotate PDF Pages Online Free - Fix PDF Orientation | SnackPDF',
        'description': 'Rotate PDF pages online for free. Fix page orientation, rotate clockwise or counterclockwise. Easy PDF rotation tool.',
        'keywords': 'rotate PDF, rotate PDF pages, fix PDF orientation, turn PDF pages, PDF rotation',
        'canonical': 'https://www.snackpdf.com/rotate'
    }
}

def create_seo_template_content(tool_name, seo_data):
    """Create template content with SEO optimization"""
    return f'''{{%% extends "base.html" %%}}

{{%% block title %%}}{seo_data['title']}{{%% endblock %%}}
{{%% block meta_title %%}}{seo_data['title']}{{%% endblock %%}}
{{%% block meta_description %%}}{seo_data['description']}{{%% endblock %%}}
{{%% block meta_keywords %%}}{seo_data['keywords']}{{%% endblock %%}}

{{%% block canonical_url %%}}{seo_data['canonical']}{{%% endblock %%}}
{{%% block og_url %%}}{seo_data['canonical']}{{%% endblock %%}}
{{%% block og_title %%}}{seo_data['title']}{{%% endblock %%}}
{{%% block og_description %%}}{seo_data['description']}{{%% endblock %%}}

{{%% block twitter_url %%}}{seo_data['canonical']}{{%% endblock %%}}
{{%% block twitter_title %%}}{seo_data['title']}{{%% endblock %%}}
{{%% block twitter_description %%}}{seo_data['description']}{{%% endblock %%}}

{{%% block structured_data %%}}
{{
    "@context": "https://schema.org",
    "@type": "WebApplication",
    "name": "{seo_data['title'].split(' | ')[0]}",
    "url": "{seo_data['canonical']}",
    "description": "{seo_data['description']}",
    "applicationCategory": "UtilitiesApplication",
    "operatingSystem": "Any",
    "offers": {{
        "@type": "Offer",
        "price": "0",
        "priceCurrency": "USD"
    }},
    "publisher": {{
        "@type": "Organization",
        "name": "SnackPDF",
        "url": "https://www.snackpdf.com"
    }}
}}
{{%% endblock %%}}

{{%% block content %%}}
<div class="tool-form-container">
    <h1>{seo_data['title'].split(' | ')[0]}</h1>
    <p>{seo_data['description']}</p>
    
    <div class="drag-drop">
        <strong>Select or drag and drop your files here</strong>
    </div>
    
    <div class="action-buttons">
        <button type="submit">Process File</button>
        <button type="button">Clear</button>
    </div>
</div>
{{%% endblock %%}}'''

def update_tool_templates():
    """Update tool templates with SEO optimization"""
    template_dir = "pdf_to_image/templates"
    
    for tool_name, seo_data in TOOL_SEO_DATA.items():
        # Update both old and new template files
        for suffix in ['', '_new']:
            filename = f"{tool_name}{suffix}.html"
            filepath = os.path.join(template_dir, filename)
            
            if os.path.exists(filepath):
                print(f"Updating {filename} with SEO optimization...")
                
                # Create optimized template content
                content = create_seo_template_content(tool_name, seo_data)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"✅ Updated {filename}")

if __name__ == "__main__":
    print("🚀 Starting tool page SEO optimization...")
    update_tool_templates()
    print("🎉 All tool pages optimized for SEO!")
