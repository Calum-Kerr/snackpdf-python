from flask import Blueprint, request, send_file
import fitz  # PyMuPDF
import os

security_bp = Blueprint('security', __name__)

STATIC_DIR = os.path.join(os.getcwd(), 'pdf_to_image', 'static')

# Ensure the static directory exists
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

@security_bp.route('/unlock', methods=['POST'])
def unlock_pdf():
    file = request.files['file']
    password = request.form['password']
    output_path = os.path.join(STATIC_DIR, f'unlocked_{file.filename}')

    try:
        pdf = fitz.open(stream=file.read(), filetype='pdf')
        if pdf.needs_pass:
            pdf.authenticate(password)
        pdf.save(output_path)
        pdf.close()
    except Exception as e:
        return {"error": str(e)}, 500

    return send_file(output_path, as_attachment=True)

@security_bp.route('/protect', methods=['POST'])
def protect_pdf():
    file = request.files['file']
    password = request.form['password']
    output_path = os.path.join(STATIC_DIR, f'protected_{file.filename}')

    try:
        pdf = fitz.open(stream=file.read(), filetype='pdf')
        pdf.save(output_path, encryption=fitz.PDF_ENCRYPT_AES_256, owner_pw=password, user_pw=password, permissions=0)  # 0 for no permissions
        pdf.close()
    except Exception as e:
        return {"error": str(e)}, 500

    return send_file(output_path, as_attachment=True)
