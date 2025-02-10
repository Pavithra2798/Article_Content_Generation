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

    blob.download_to_filename(path+'/files/local-file.txt')

    with open(path+'/files/local-file.txt', 'r') as file:
        file_content = file.read()
    return file_content


def convert_mono(text_file):

    # Upload the mono audio file to GCS
    mono_audio_file = path + "/files/call_transcript.txt"
    mono_gcs_path = text_file
    file_content = upload_to_gcs(mono_audio_file, mono_gcs_path, "<project-id>")

    summary_text = generate_text(file_content)
    print(summary_text)
    return summary_text

def to_markdown(text):
  text = text.replace('•', '  *')
  return Markdown(textwrap.indent(text, '> ', predicate=lambda _: True))

def generate_text(response) -> str:

    multimodal_model = GenerativeModel("gemini-pro")
    response = multimodal_model.generate_content(f'''The below is a sample call transcriptions {response}.
    explain about each unique customer. Consider account number as unique value to identify unique 
    customer. Provide details like:

    Account Number
    Date of Call
    Customer Name
    Payment Due Date
    Amount Due
    Reason for Missed Payment
    Payment Commitment
    Extension Granted
    Follow-up Date
    Resolution Status
    Payment History
    Preferred Communication Channel
    Customer Satisfaction
    Payment Method
 
    All the above points should be in 2-3 words that can be easily stored in a excel file.

    Do not format using markdown language. 
    You are an AI assistant that can generate HTML and CSS code for creating visually effective document
    content.
    Please ensure to format the output data in a table format using HTML tags, and apply professional CSS 
    styles to enhance the visual presentation. Utilize the <table> tag to structure the data in a 
    tabular format, and consider using <th> for table headers and <td> for table data. Additionally, 
    apply CSS styles to the table, such as specifying colors for headers, use only balck and #053e91 colors 
    for styling and overall styling to improve the visual appeal. Please ensure that the 
    table formatting and CSS styles are consistently and effectively applied to enhance the 
    presentation of the output data. If any of the field value value is not available, add "None" 
    and then create a formatted table. Please make sure to add table structure to the output data
    and ensure that you are not using markdown language or | to seperate the fields of the table.
    If the output data still contains markdown language or | symbol, change it to HTML formatting. 
    ''')

    print(response.text)
    to_markdown(response.text)
    return response.text

