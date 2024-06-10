from flask import Blueprint, request, send_file
import fitz  # PyMuPDF
import os
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

pdf_to_word_bp = Blueprint('pdf_to_word', __name__)

STATIC_DIR = os.path.join(os.getcwd(), 'pdf_to_image', 'static')

# Ensure the static directory exists
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

@pdf_to_word_bp.route('/pdf_to_word', methods=['POST'])
def pdf_to_word():
    file = request.files['file']
    file_path = os.path.join(STATIC_DIR, file.filename)
    file.save(file_path)

    doc = fitz.open(file_path)
    word_doc = Document()

    for page_number in range(len(doc)):
        page = doc.load_page(page_number)
        text = page.get_text("text")

        if text:
            paragraph = word_doc.add_paragraph()
            run = paragraph.add_run(text)
            run.font.size = Pt(12)
            paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT

    word_doc_path = os.path.join(STATIC_DIR, f'{os.path.splitext(file.filename)[0]}.docx')
    word_doc.save(word_doc_path)

    return send_file(word_doc_path, as_attachment=True)
