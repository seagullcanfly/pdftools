from flask import Flask, request, send_file, render_template
from google.cloud import vision
import os

app = Flask(__name__)

# Configure Google Cloud Vision credentials - IMPORTANT: Use environment variable!
# os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'path/to/your/credentials.json'  # REMOVE THIS LINE FOR PRODUCTION
# We'll set this on Render as an environment variable

def transcribe_pdf(pdf_file_path):
    """Transcribes text from a PDF file using Google Cloud Vision API."""
    client = vision.ImageAnnotatorClient()

    with open(pdf_file_path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)
    response = client.document_text_detection(image=image)
    text = response.full_text_annotation.text if response.full_text_annotation else ""
    return text

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'pdf_file' not in request.files:
            return "No file part"

        pdf_file = request.files['pdf_file']
        if pdf_file.filename == '':
            return "No selected file"

        if pdf_file:
            temp_pdf_path = "temp_pdf.pdf"  # Temporary file to save uploaded PDF
            pdf_file.save(temp_pdf_path)

            transcribed_text = transcribe_pdf(temp_pdf_path)
            os.remove(temp_pdf_path)  # Clean up temporary file

            text_file_path = "transcribed_text.txt"
            with open(text_file_path, 'w') as f:
                f.write(transcribed_text)

            return send_file(text_file_path, as_attachment=True, download_name="transcribed_text.txt")

    return render_template('index.html')  # Or a simple HTML form directly here if you don't want templates

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000)) # Get port from environment variable, default to 5000
    app.run(host='0.0.0.0', port=port, debug=True) # Bind to 0.0.0.0 and use dynamic port