from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
import random
import speech_recognition as sr
from pydub import AudioSegment

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a random secret key
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# In-memory user storage for demonstration purposes
users = {}

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    if user_id in users:
        return User(user_id)
    return None

def generate_random_letter():
    letters = 'abcdefghijklmnopqrstuvwxyz'
    words = ["apple", "green", "one", "two", "white", "house", "mountian", "brilliant", "chair", "table", "water"]
    return random.choice(words)

def calculate_letter_recognition_score(expected_letter, spoken_letter):
    expected_letter = expected_letter.lower()
    spoken_letter = spoken_letter.lower()

    if expected_letter == spoken_letter:
        return 1.0
    else:
        return 0.0

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users:
            return 'Username already exists', 400
        users[username] = {'password': password}
        user = User(username)
        login_user(user)
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username]['password'] == password:
            user = User(username)
            login_user(user)
            return redirect(url_for('index'))
        return 'Invalid credentials', 401
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    expected_letters = [generate_random_letter() for _ in range(5)]
    return render_template('index.html', expected_letters=expected_letters)

@app.route('/upload', methods=['POST'])
@login_required
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