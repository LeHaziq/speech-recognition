from flask import Flask, render_template, request, jsonify
import os
import random
import speech_recognition as sr
from pydub import AudioSegment

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def generate_random_letter():
    return random.choice('abcdefghijklmnopqrstuvwxyz')

def calculate_letter_recognition_score(expected_letter, spoken_letter):
    expected_letter = expected_letter.lower()
    spoken_letter = spoken_letter.lower()

    if expected_letter == spoken_letter:
        return 1.0
    else:
        return 0.0

@app.route('/')
def index():
    expected_letters = [generate_random_letter() for _ in range(5)]
    return render_template('index.html', expected_letters=expected_letters)

@app.route('/upload', methods=['POST'])
def upload():
    expected_letters = request.form.getlist('expected_letters[]')
    total_score = 0.0
    transcriptions = []

    for i in range(5):
        if f'audio_data_{i}' in request.files:
            audio_file = request.files[f'audio_data_{i}']
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
                    spoken_letter = recognizer.recognize_google(audio_data)
                except sr.UnknownValueError:
                    spoken_letter = ""
                except sr.RequestError:
                    spoken_letter = ""

            score = calculate_letter_recognition_score(expected_letters[i], spoken_letter)
            total_score += score
            transcriptions.append(spoken_letter)

    return jsonify({
        'message': 'Audio uploaded successfully',
        'transcriptions': transcriptions,
        'expected_letters': expected_letters,
        'total_score': total_score
    }), 200

if __name__ == '__main__':
    app.run(debug=True)