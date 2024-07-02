from flask import Flask, render_template, request
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'audio_data' in request.files:
        audio_file = request.files['audio_data']
        audio_file.save(os.path.join(UPLOAD_FOLDER, audio_file.filename))
        return 'Audio uploaded successfully', 200
    return 'No audio file found', 400

if __name__ == '__main__':
    app.run(debug=True)