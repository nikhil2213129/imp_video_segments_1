from flask import Flask, request, render_template, send_file
from moviepy.editor import VideoFileClip
import speech_recognition as sr
import spacy
import os

app = Flask(__name__)

def video_to_audio(video_path, audio_path):
    video = VideoFileClip(video_path)
    audio = video.audio
    audio.write_audiofile(audio_path)

def audio_to_text(audio_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data)  # Removed timeout
        except sr.RequestError as e:
            return f"Could not request results from Google Speech Recognition service; {e}"
        except sr.UnknownValueError:
            return "Google Speech Recognition could not understand audio"
    return text

def extract_important_text(text):
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    important_sentences = []

    for sent in doc.sents:
        if any(ent.label_ in ['PERSON', 'ORG', 'GPE'] for ent in sent.ents):
            important_sentences.append(sent.text)

    return important_sentences

@app.route('/')
def upload_form():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    if file:
        video_path = os.path.join('uploads', file.filename)
        file.save(video_path)

        audio_path = "output_audio.wav"
        video_to_audio(video_path, audio_path)
        text = audio_to_text(audio_path)

        important_sentences = extract_important_text(text)
        timestamps = [10, 20, 30]  # Modify as needed
        important_video = VideoFileClip(video_path).subclip(timestamps[0], timestamps[-1])
        important_video_path = "important_segments.mp4"
        important_video.write_videofile(important_video_path)

        return send_file(important_video_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)