from flask import Flask, request, send_file, render_template
from google.cloud import vision
import os
import json
from google.oauth2 import service_account

app = Flask(__name__)

def transcribe_pdf(pdf_file_path):
    """Transcribes text from a PDF file using Google Cloud Vision API."""

    # 1. Get the JSON credentials content from the environment variable
    credentials_json_str = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS_JSON')

    if not credentials_json_str: # Check if the env var is set (critical!)
        raise Exception("Environment variable GOOGLE_APPLICATION_CREDENTIALS_JSON is not set!")

    try:
        # 2. Load the JSON string into a dictionary (Python object)
        credentials_info = json.loads(credentials_json_str)

        # 3. Create credentials object from info - EXPLICITLY set project_id
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info,
            project_id=credentials_info.get('project_id') # Explicitly pass project_id
        )

        # 4. Create the Vision client, explicitly passing the credentials
        client = vision.ImageAnnotatorClient(credentials=credentials)

    except Exception as e: # Catch any credential loading errors
        print(f"Credential Loading Error: {e}") # Print detailed error to logs!
        raise # Re-raise the exception to be caught by index() error handling

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

            try:
                transcribed_text = transcribe_pdf(temp_pdf_path)
                os.remove(temp_pdf_path)

                text_file_path = "transcribed_text.txt"
                with open(text_file_path, 'w') as f:
                    f.write(transcribed_text)

                return send_file(text_file_path, as_attachment=True, download_name="transcribed_text.txt")
            except Exception as e:
                os.remove(temp_pdf_path)
                return f"Transcription Error: {str(e)}"

    return render_template('index.html')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)