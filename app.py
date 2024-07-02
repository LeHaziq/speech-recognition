from flask import Flask, render_template, request, jsonify
import os
import speech_recognition as sr
from pydub import AudioSegment

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
        file_path = os.path.join(UPLOAD_FOLDER, audio_file.filename)
        audio_file.save(file_path)

        # Convert audio to PCM WAV format
        audio = AudioSegment.from_file(file_path)
        wav_path = file_path.replace('.webm', '.wav')
        audio.export(wav_path, format='wav')

        # Recognize the audio
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio_data)
            except sr.UnknownValueError:
                text = "Could not understand audio"
            except sr.RequestError:
                text = "Could not request results; check your network connection"

        return jsonify({'message': 'Audio uploaded successfully', 'transcription': text}), 200
    return 'No audio file found', 400

if __name__ == '__main__':
    app.run(debug=True)