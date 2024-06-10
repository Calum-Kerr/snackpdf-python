from flask import Blueprint, request, send_file
import fitz  # PyMuPDF
import os
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

pdf_to_word_bp = Blueprint('pdf_to_word', __name__)

STATIC_DIR = os.path.join(os.getcwd(), 'pdf_to_image', 'static')

# Ensure the static directory exists
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

def add_paragraph_with_formatting(doc, text, font_size=12, bold=False, italic=False, underline=False, color=None, bullet=False):
    paragraph = doc.add_paragraph(style='List Bullet' if bullet else None)
    run = paragraph.add_run(text)
    run.font.size = Pt(font_size)
    run.bold = bold
    run.italic = italic
    run.underline = underline
    if color and isinstance(color, tuple) and len(color) == 3:
        run.font.color.rgb = RGBColor(color[0], color[1], color[2])
    paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT

    # Set spacing to default
    paragraph_format = paragraph.paragraph_format
    paragraph_format.space_after = Pt(0)
    paragraph_format.space_before = Pt(0)
    paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE

def add_table(doc, table_data):
    table = doc.add_table(rows=len(table_data), cols=len(table_data[0]))
    table.style = 'Table Grid'
    for row_idx, row_data in enumerate(table_data):
        for col_idx, cell_data in enumerate(row_data):
            cell = table.cell(row_idx, col_idx)
            cell.text = cell_data
            # Apply default font size to table cells
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(12)
                    run.font.name = 'Calibri'
                    run.bold = False
                    run.italic = False
                    run.underline = False
    return table

def add_hyperlink(paragraph, url, text, font_size=12, color=RGBColor(0, 0, 255)):
    """
    A function that places a hyperlink within a paragraph object.
    """
    part = paragraph.part
    r_id = part.relate_to(url, 'hyperlink', is_external=True)

    hyperlink = OxmlElement('w:hyperlink')
    hyperlink.set(qn('r:id'), r_id, )

    new_run = OxmlElement('w:r')
    rPr = OxmlElement('w:rPr')

    # Apply formatting
    r_style = OxmlElement('w:rStyle')
    r_style.set(qn('w:val'), 'Hyperlink')
    rPr.append(r_style)
    new_run.append(rPr)

    text_run = OxmlElement('w:t')
    text_run.text = text
    new_run.append(text_run)

    hyperlink.append(new_run)
    paragraph._p.append(hyperlink)

@pdf_to_word_bp.route('/pdf_to_word', methods=['POST'])
def pdf_to_word():
    file = request.files['file']
    file_path = os.path.join(STATIC_DIR, file.filename)
    file.save(file_path)

    doc = fitz.open(file_path)
    word_doc = Document()

    for page_number in range(len(doc)):
        page = doc.load_page(page_number)
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            if block["type"] == 0:  # Text block
                text = block["lines"]
                for line in text:
                    spans = line["spans"]
                    for span in spans:
                        font_size = span["size"]
                        text_content = span["text"]
                        color_int = span.get("color", 0)
                        # Convert color int to RGB tuple
                        color = [(color_int >> 16) & 0xff, (color_int >> 8) & 0xff, color_int & 0xff]

                        if span.get("flags", 0) & 2:  # Check if the span is a link
                            url = span.get("uri")
                            if url:
                                add_hyperlink(word_doc.add_paragraph(), url, text_content, font_size, RGBColor(*color))
                        else:
                            add_paragraph_with_formatting(word_doc, text_content, font_size=font_size, color=color)

            elif block["type"] == 1:  # Image block (can be extended to handle images if needed)
                pass

            elif block["type"] == 2:  # Table block
                table_data = []
                for line in block["lines"]:
                    row = []
                    for span in line["spans"]:
                        row.append(span["text"])
                    table_data.append(row)
                print("Extracted table data:", table_data)  # Debug print statement
                if table_data:
                    add_table(word_doc, table_data)

            elif block["type"] == 3:  # Bullet points
                for line in block["lines"]:
                    for span in line["spans"]:
                        add_paragraph_with_formatting(word_doc, span["text"], font_size=span["size"], bullet=True)

        # Add a page break after each page except the last one
        if page_number < len(doc) - 1:
            word_doc.add_page_break()

    word_doc_path = os.path.join(STATIC_DIR, f'{os.path.splitext(file.filename)[0]}.docx')
    word_doc.save(word_doc_path)

    return send_file(word_doc_path, as_attachment=True)
