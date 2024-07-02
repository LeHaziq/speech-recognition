def generate_random_letter():
    return random.choice('abcdefghijklmnopqrstuvwxyz')

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Record Audio</title>
</head>
<body>
    <h1>Record Audio</h1>
    <button id="recordButton">Record</button>
    <button id="stopButton" disabled>Stop</button>
    <button id="playButton" disabled>Play</button>
    <audio id="audioPlayback" controls></audio>
    <p id="transcription"></p>
    <script>
        let mediaRecorder;
        let audioChunks = [];
        let audioBlob;

        document.getElementById('recordButton').onclick = async () => {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.start();

            mediaRecorder.ondataavailable = event => {
                audioChunks.push(event.data);
            };

            mediaRecorder.onstop = async () => {
                audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                const formData = new FormData();
                formData.append('audio_data', audioBlob, 'recording.wav');

                await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });

                const audioUrl = URL.createObjectURL(audioBlob);
                document.getElementById('audioPlayback').src = audioUrl;

                audioChunks = [];
                document.getElementById('playButton').disabled = false;

                // Speech Recognition
                const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
                recognition.lang = 'en-US';
                recognition.interimResults = false;
                recognition.maxAlternatives = 1;

                recognition.onresult = (event) => {
                    const transcript = event.results[0][0].transcript;
                    document.getElementById('transcription').innerText = `Transcription: ${transcript}`;
                };

                recognition.onerror = (event) => {
                    document.getElementById('transcription').innerText = `Error: ${event.error}`;
                };

                const audioContext = new AudioContext();
                const reader = new FileReader();
                reader.readAsArrayBuffer(audioBlob);
                reader.onloadend = () => {
                    audioContext.decodeAudioData(reader.result, (buffer) => {
                        const source = audioContext.createBufferSource();
                        source.buffer = buffer;
                        const processor = audioContext.createScriptProcessor(4096, 1, 1);
                        source.connect(processor);
                        processor.connect(audioContext.destination);
                        processor.onaudioprocess = (e) => {
                            recognition.start();
                            processor.disconnect();
                        };
                        source.start(0);
                    });
                };
            };

            document.getElementById('recordButton').disabled = true;
            document.getElementById('stopButton').disabled = false;
        };

        document.getElementById('stopButton').onclick = () => {
            mediaRecorder.stop();
            document.getElementById('recordButton').disabled = false;
            document.getElementById('stopButton').disabled = true;
        };

        document.getElementById('playButton').onclick = () => {
            document.getElementById('audioPlayback').play();
        };
    </script>
</body>
</html>