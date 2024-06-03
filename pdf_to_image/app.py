from flask import Flask, request, send_file, render_template
from pdf2image import convert_from_path
from PIL import Image
import os
import zipfile

app = Flask(__name__)
STATIC_DIR = os.path.join(os.getcwd(), 'pdf_to_image', 'static')

# Ensure the static directory exists
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    file = request.files['file']
    file_path = os.path.join(STATIC_DIR, file.filename)
    file.save(file_path)

    images = convert_from_path(file_path)
    image_paths = []
    for i, image in enumerate(images):
        image_path = os.path.join(STATIC_DIR, f'{file.filename}_page_{i + 1}.jpg')
        image.save(image_path, 'JPEG')
        image_paths.append(image_path)

    # Create a ZIP file containing all the images
    zip_path = os.path.join(STATIC_DIR, f'{file.filename}.zip')
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for image_path in image_paths:
            zipf.write(image_path, os.path.basename(image_path))

    # Send the ZIP file
    return send_file(zip_path, as_attachment=True)

@app.route('/panoramic', methods=['POST'])
def panoramic():
    file = request.files['file']
    file_path = os.path.join(STATIC_DIR, file.filename)
    file.save(file_path)

    images = convert_from_path(file_path)
    widths, heights = zip(*(i.size for i in images))

    total_width = sum(widths)
    max_height = max(heights)

    panoramic_image = Image.new('RGB', (total_width, max_height))
    x_offset = 0
    for image in images:
        panoramic_image.paste(image, (x_offset, 0))
        x_offset += image.width

    panoramic_image_path = os.path.join(STATIC_DIR, f'{file.filename}_panoramic.jpg')
    panoramic_image.save(panoramic_image_path, 'JPEG')

    return send_file(panoramic_image_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
