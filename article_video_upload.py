from flask import Flask, render_template, request, jsonify
import article_generation
import os
import call_transcript

app = Flask(__name__)

@app.route('/')
def upload_page():
    return render_template('article_processing.html')

@app.route('/summarizeVideo')
def summarizeVideo():   
    return render_template('call_transcript_processing.html')

@app.route('/process_transcript', methods=['POST'])
def process_transcript():
    text_file = request.json.get('url')
    print(text_file)
    transcript_analysis = call_transcript.convert_mono(text_file)
    return jsonify({'video_summary': transcript_analysis})  

@app.route('/process_video', methods=['POST'])
def process_video():
    recording_video = request.files['videoFile']
    wordcount = request.form['wordcount']

    video_path = '/tmp/recording_video.mp4'

    recording_video.save(video_path)
    summary_text = article_generation.convert_mono(video_path,wordcount)

    output_text = summary_text
    os.remove(video_path)

    return jsonify({'article_summary': output_text})  

if __name__ == '__main__':
    # app.run(debug=True)
    app.run(debug=True, port=8080)
