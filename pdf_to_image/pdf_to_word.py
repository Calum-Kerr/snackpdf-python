from flask import Flask, Blueprint, request, send_file
import fitz  # PyMuPDF
import os
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from PIL import Image
import io

app = Flask(__name__)
pdf_to_word_bp = Blueprint('pdf_to_word', __name__)

STATIC_DIR = os.path.join(os.getcwd(), 'static')

# Ensure the static directory exists
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

def set_run_style(run, font_name, font_size, font_color, bold, italic, underline):
    run.font.name = font_name
    run.font.size = Pt(font_size)
    run.font.color.rgb = RGBColor(font_color[0], font_color[1], font_color[2])
    run.bold = bold
    run.italic = italic
    run.underline = underline

def add_paragraph_with_formatting(doc, text, font_name='Arial', font_size=12, bold=False, italic=False, underline=False, color=(0, 0, 0), alignment=WD_PARAGRAPH_ALIGNMENT.LEFT):
    paragraph = doc.add_paragraph()
    run = paragraph.add_run(text)
    set_run_style(run, font_name, font_size, color, bold, italic, underline)
    paragraph.alignment = alignment
    paragraph_format = paragraph.paragraph_format
    paragraph_format.space_after = Pt(0)
    paragraph_format.space_before = Pt(0)
    paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE

def add_table(doc, table_data):
    try:
        if not table_data:
            return
        table = doc.add_table(rows=len(table_data), cols=max(len(row) for row in table_data))
        table.style = 'Table Grid'
        for row_idx, row_data in enumerate(table_data):
            for col_idx, cell_data in enumerate(row_data):
                cell = table.cell(row_idx, col_idx)
                cell.text = cell_data
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.size = Pt(12)
                        run.font.name = 'Calibri'
    except Exception as e:
        print(f"Error adding table: {e}")

def add_hyperlink(paragraph, url, text):
    part = paragraph.part
    r_id = part.relate_to(url, "hyperlink", is_external=True)
    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), r_id)
    new_run = OxmlElement("w:r")
    r_pr = OxmlElement("w:rPr")
    r_style = OxmlElement("w:rStyle")
    r_style.set(qn("w:val"), "Hyperlink")
    r_pr.append(r_style)
    new_run.append(r_pr)
    text_run = OxmlElement("w:t")
    text_run.text = text
    new_run.append(text_run)
    hyperlink.append(new_run)
    paragraph._p.append(hyperlink)

def add_image(doc, image_stream, width, height):
    try:
        image = Image.open(image_stream)
        image_stream.seek(0)
        doc.add_picture(image_stream, width=Inches(width / 96), height=Inches(height / 96))
    except Exception as e:
        print(f"Error adding image: {e}")

def extract_text_and_styles(page):
    text_elements = []
    blocks = page.get_text("dict")["blocks"]
    for block in blocks:
        if block["type"] == 0:  # Text block
            for line in block["lines"]:
                for span in line["spans"]:
                    text_elements.append({
                        "text": span["text"],
                        "font": span["font"],
                        "size": span["size"],
                        "color": [(span["color"] >> 16) & 0xff, (span["color"] >> 8) & 0xff, span["color"] & 0xff],
                        "flags": span["flags"],
                        "bbox": span["bbox"]
                    })
    return text_elements

def extract_images(page):
    images = []
    image_list = page.get_images(full=True)
    for img in image_list:
        xref = img[0]
        try:
            base_image = fitz.Pixmap(page.parent, xref)
            if base_image.n > 4:  # Convert CMYK and other modes to RGB first
                base_image = fitz.Pixmap(fitz.csRGB, base_image)
            image_bytes = base_image.tobytes("png")
            bbox = img[3] if isinstance(img[3], (list, tuple)) else [0, 0, base_image.width, base_image.height]
            images.append({
                "image": image_bytes,
                "bbox": bbox
            })
        except Exception as e:
            print(f"Error extracting image {xref}: {e}")
    return images

def extract_tables(page):
    tables = []
    blocks = page.get_text("dict")["blocks"]
    current_table = []
    previous_bottom = None
    
    for block in blocks:
        if block["type"] == 0:  # Text block
            block_top = block['bbox'][1]
            block_bottom = block['bbox'][3]
            if previous_bottom is not None and block_top - previous_bottom > 10:  # Arbitrary gap to detect new table
                if current_table:
                    tables.append(current_table)
                    current_table = []
            row = []
            for line in block["lines"]:
                row_text = " ".join([span["text"] for span in line["spans"]])
                row.append(row_text)
            current_table.append(row)
            previous_bottom = block_bottom
    
    if current_table:
        tables.append(current_table)
    
    # Normalize table row lengths
    max_columns = max(len(row) for table in tables for row in table)
    for table in tables:
        for row in table:
            while len(row) < max_columns:
                row.append("")  # Fill missing cells with empty strings

    return tables

@pdf_to_word_bp.route('/pdf_to_word', methods=['POST'])
def pdf_to_word():
    try:
        file = request.files['file']
        file_path = os.path.join(STATIC_DIR, file.filename)
        file.save(file_path)

        doc = fitz.open(file_path)
        word_doc = Document()

        # Add a header and footer
        section = word_doc.sections[0]
        header = section.header
        footer = section.footer

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)

            # Extract and add text elements
            text_elements = extract_text_and_styles(page)
            for elem in text_elements:
                add_paragraph_with_formatting(
                    word_doc,
                    elem["text"],
                    font_size=elem["size"],
                    color=elem["color"],
                    bold=bool(elem["flags"] & 2),
                    italic=bool(elem["flags"] & 1),
                    underline=bool(elem["flags"] & 4),
                    alignment=WD_PARAGRAPH_ALIGNMENT.LEFT  # Customize alignment as needed
                )

            # Extract and add images
            images = extract_images(page)
            for img in images:
                image_stream = io.BytesIO(img["image"])
                bbox = img["bbox"]
                if isinstance(bbox, (list, tuple)) and len(bbox) == 4:
                    width = bbox[2] - bbox[0]
                    height = bbox[3] - bbox[1]
                    add_image(word_doc, image_stream, width, height)
                else:
                    # Handle unexpected bbox format
                    print(f"Unexpected bbox format: {bbox}")

            # Extract and add tables
            tables = extract_tables(page)
            for table in tables:
                add_table(word_doc, table)

            if page_num < len(doc) - 1:
                word_doc.add_page_break()

        word_doc_path = os.path.join(STATIC_DIR, f'{os.path.splitext(file.filename)[0]}.docx')
        word_doc.save(word_doc_path)

        return send_file(word_doc_path, as_attachment=True)
    except Exception as e:
        print(f"Error during PDF to Word conversion: {e}")
        return {"error": str(e)}, 500

app.register_blueprint(pdf_to_word_bp)

if __name__ == '__main__':
    app.run(debug=True)
