# pip install moviepy
# pip install SpeechRecognition
# pip install soundfile
# pip install google-cloud-speech
# pip install "google-cloud-aiplatform>=1.38"
# pip3 install --upgrade --user google-cloud-aiplatform
# pip install ipython
# pip install youtube-transcript-api
# gcloud auth application-default login
# gcloud auth application-default set-quota-project <project-id>

import io
from google.cloud import speech
import moviepy.editor as mp
import soundfile as sf
import speech_recognition as sr
import pathlib
import textwrap
from IPython.display import display
from IPython.display import Markdown
import vertexai
from google.cloud import storage
from vertexai.preview.generative_models import GenerativeModel
import os
import base64


vertexai.init(project="<project-id>", location="us-central1")
from vertexai.preview.generative_models import GenerativeModel, Part


path = os.path.dirname(os.path.realpath(__file__))
print(path)

bucket_name = "article_creation_bucket"

def upload_to_gcs(local_file_path, gcs_file_path, project_id):
    storage_client = storage.Client(project=project_id)
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(gcs_file_path)
    blob.upload_from_filename(local_file_path)

def convert_mono(recording_video,wordcount):
    audio_file = path + "/files/output_audio.wav"
    print(type(recording_video))
    print(recording_video)
    
    video_clip = mp.VideoFileClip(recording_video)

    # Split the video into 1-minute segments
    segment_duration = 60  # in seconds
    total_duration = video_clip.duration
    segments = []
    start_time = 0
    while start_time < total_duration:
        end_time = min(start_time + segment_duration, total_duration)
        segment = video_clip.subclip(start_time, end_time)
        segments.append(segment)
        start_time += segment_duration

    # Process each segment and concatenate the audio
    audio_clips = [segment.audio for segment in segments]
    concatenated_audio = mp.concatenate_audioclips(audio_clips)
    concatenated_audio.write_audiofile(audio_file)

    # Convert to mono channel
    data, samplerate = sf.read(audio_file)
    mono_data = data[:, 0]
    mono_audio_file = path + "/files/mono_audio.wav"
    sf.write(mono_audio_file, mono_data, samplerate)

    mono_gcs_path = "mono_audio.wav"
    upload_to_gcs(mono_audio_file, mono_gcs_path, "<project-id>")

    # Use LongRunningRecognize with the URI of the audio file
    client = speech.SpeechClient()
    gcs_uri = f"gs://{bucket_name}/{mono_gcs_path}"
    audio = speech.RecognitionAudio(uri=gcs_uri)
    config = speech.RecognitionConfig(
        encoding=1,
        # sample_rate_hertz=16000,
        language_code="en-US",
    )

    operation = client.long_running_recognize(config=config, audio=audio)
    response = operation.result()

    summary_text = generate_text(response.results,wordcount)
    return summary_text

def to_markdown(text):
  text = text.replace('•', '  *')
  return Markdown(textwrap.indent(text, '> ', predicate=lambda _: True))

def generate_text(response,wordcount) -> str:

    multimodal_model = GenerativeModel("gemini-pro")
    response = multimodal_model.generate_content(f'''
    
    You are a host of a meeting.You need to write an article for this content {response}. 
    Write the article in such a way that the readers get an essence of the meeting.
    Correctly capture the details of the speaker as well. Start the article with an overview of the 
    meeting and specifically include the details about the speaker if available.
    Do not misinterpret and give a fake name for the speaker. Only provide the speaker details if you 
    are very sure or else mention "speaker" instead of giving a fake name.
    Capture the essence of the meeting by sharing the speaker's valuable insights, real-world examples, 
    and practical advice. Describe the audience's engagement and mindset during the meeting, highlighting their 
    receptiveness to the speaker's message. Mention any memorable quotes or moments from the meeting that 
    resonated with the audience. To make the article more interesting, include impressive dialogues from the 
    speaker and provide specific examples of the concepts discussed. Use vivid language to paint a picture of 
    the meeting in the reader's mind. Write the article from the host's perspective, ensuring that the content 
    is engaging, informative, and accurately reflects the essence of the meeting. 
    Write the article in about { wordcount } words.
    
    Do not format using markdown language. You are an AI assistant that can generate HTML and CSS code for creating 
    visually effective document content. Please ensure that all content in the output is consistently formatted 
    using HTML tags for visual enhancement. Use HTML tags such as <b> for bold text, <i> for italics, <ul> and <ol> 
    for lists, <p> for paragraphs and <h2> for headings. 
    Additionally, apply CSS styles for proper layout, typography, colors, and any other visual enhancements. 
    If applicable, utilize <div> and <span> for structuring and styling the quotes of the speaker.
    It's essential that the HTML formatting and CSS styles are applied uniformly and
    effectively to elevate the visual appeal of the output. Apply CSS styles to specify different colors 
    for each heading level. Use #59c4d3 only for <h1> and <h2> tags. Justify only the <h1> tag to centre.
    The use of colors should align with the overall design and visual appeal of 
    the output. Consistency in color choices and readability should be considered when applying 
    these styles. Please pay close attention to applying HTML tags and CSS styles consistently and 
    comprehensively and ensure that you are not using markdown language.

    ''')


    print(response.text)
    to_markdown(response.text)
    return response.text

