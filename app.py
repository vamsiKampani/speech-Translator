from flask import Flask, request, render_template, jsonify, send_from_directory
import sounddevice as sd
from scipy.io.wavfile import write
import speech_recognition as spr
from googletrans import Translator
from gtts import gTTS
import os
import tempfile

app = Flask(__name__, static_folder='outputs')

recog1 = spr.Recognizer()

language_map = {
    'Hindi': 'hi',
    'Telugu': 'te',
    'Kannada': 'kn',
    'Tamil': 'ta',
    'Malayalam': 'ml',
    'Bengali': 'bn'
}

def recognize_speech(recog):
    try:
        print("Recording audio using SoundDevice...")
        
        # Recording parameters
        duration = 10  # seconds
        samplerate = 44100  # Sample rate in Hz
        
        # Record audio
        print("Listening...")
        audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
        sd.wait()  # Wait until recording is finished
        
        # Save audio to a temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            write(temp_file.name, samplerate, audio)
            temp_wav_path = temp_file.name
        
        print("Processing audio...")
        
        # Process the recorded audio with speech_recognition
        with spr.AudioFile(temp_wav_path) as source:
            audio_data = recog.record(source)
            recognized_text = recog.recognize_google(audio_data)
        
        # Cleanup temporary file
        os.remove(temp_wav_path)
        return recognized_text
    
    except spr.UnknownValueError:
        print("Google Speech Recognition could not understand the audio.")
        return None
    except spr.RequestError as e:
        print(f"Request error: {e}")
        return None
    except Exception as e:
        print(f"Error during speech recognition: {e}")
        return None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/translate', methods=['POST'])
def translate_speech():
    data = request.json
    target_language_input = data.get('targetLanguage', '').strip()

    if target_language_input not in language_map:
        return jsonify({"error": "Invalid language. Please enter a valid language."}), 400

    target_language_code = language_map[target_language_input]

    try:
        print("Listening for speech input...")
        MyText = recognize_speech(recog1)

        if not MyText:
            return jsonify({"error": "No speech input detected. Please try again."}), 400

        print(f"Recognized Text: {MyText}")
        translator = Translator()
        detected_language = translator.detect(MyText).lang
        print(f"Detected Language: {detected_language}")

        if not os.path.exists('outputs'):
            os.makedirs('outputs')

        text_to_translate = translator.translate(MyText, src=detected_language, dest=target_language_code)
        translated_text = text_to_translate.text
        print(f"Translated Text in {target_language_input}: {translated_text}")

        audio_file = f"outputs/captured_voice_{target_language_input}.mp3"
        speak = gTTS(text=translated_text, lang=target_language_code, slow=False)
        speak.save(audio_file)

        return jsonify({
            "recognizedText": MyText,
            "translatedText": translated_text,
            "audioUrl": f"/audio/captured_voice_{target_language_input}.mp3"
        })

    except Exception as e:
        print(f"Error during translation process: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/audio/<filename>')
def send_audio(filename):
    return send_from_directory('outputs', filename)

if __name__ == '__main__':
    if not os.path.exists('outputs'):
        os.makedirs('outputs')
    app.run(debug=False)



