from flask import Flask, request, render_template, jsonify, send_from_directory
import speech_recognition as spr
from googletrans import Translator
from gtts import gTTS
import os

app = Flask(__name__, static_folder='outputs')

recog1 = spr.Recognizer()
mc = spr.Microphone()

language_map = {
    'Hindi': 'hi',
    'Telugu': 'te',
    'Kannada': 'kn',
    'Tamil': 'ta',
    'Malayalam': 'ml',
    'Bengali': 'bn'
}

def recognize_speech(recog, source):
    try:
        print("Adjusting for ambient noise...")
        recog.adjust_for_ambient_noise(source, duration=0.2)
        print("Listening...")
        audio = recog.listen(source, timeout=20, phrase_time_limit=30)
        print("Processing audio...")
        recognized_text = recog.recognize_google(audio)
        return recognized_text
    except spr.UnknownValueError:
        print("Google Speech Recognition could not understand the audio.")
        return None
    except spr.RequestError as e:
        print(f"Request error: {e}")
        return None
    except spr.WaitTimeoutError:
        print("Speech input timed out.")
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
        with mc as source:
            print("Listening for speech input...")
            MyText = recognize_speech(recog1, source)

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


