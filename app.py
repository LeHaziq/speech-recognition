from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, Score
import os
import random
import speech_recognition as sr
from pydub import AudioSegment

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a random secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize SQLAlchemy
db.init_app(app)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

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
        age = request.form['age']
        if User.query.filter_by(username=username).first():
            return 'Username already exists', 400
        new_user = User(username=username, password=password, age=age)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == ['POST']:
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
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
    return render_template('index.html', expected_letters=expected_letters, username=current_user.username, age=current_user.age)

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

    # Save the score to the database
    new_score = Score(user_id=current_user.id, score=total_score)
    db.session.add(new_score)
    db.session.commit()

    return jsonify({
        'message': 'Audio uploaded successfully',
        'transcriptions': transcriptions,
        'expected_letters': expected_letters,
        'total_score': total_score
    }), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)