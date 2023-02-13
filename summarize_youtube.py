import pandas as pd
import numpy as np
import streamlit as st
import whisper
from pytube import YouTube
from streamlit_chat import message
# import openai
# from openai.embeddings_utils import get_embedding, distances_from_embeddings
import os
import sys
import cohere
from youtube_transcript_api import YouTubeTranscriptApi
import re
from time import time,sleep


def get_video_id_from_video_id_or_url(video_id_or_url):
  # if the video id is longer than 11 characters, then it's a url
  if len(video_id_or_url) > 11:
      # if it's a url, cut it into a video id
      return video_id_or_url[-11:]
  else:
      # it's a video id
      return video_id_or_url

def get_chunks_from_youtube(video_id):
    # fetch the transcript of the video, and chunk it into 10min intervals
    transcript = YouTubeTranscriptApi.get_transcript(video_id)

    chunks = []

    start_timestamp = 0.0
    current_timestamp_mins = 0.0

    current_chunk = []

    for entry in transcript:
        current_timestamp_mins = entry['start'] / 60.0

        # specify the 5 min chunks. this can be changed into less minutes if max_token error pops up. 
        if current_timestamp_mins - start_timestamp > 5:
            # append the chunks into an array
            chunks.append(current_chunk)
            # reset the start timestamp
            start_timestamp = current_timestamp_mins
            # reset the current chunk
            current_chunk = []

        # add the line to the current chunk
        current_chunk.append(entry['text'])

    # add the last chunk
    if len(current_chunk) > 0:
        chunks.append(current_chunk)

    print(f"Found {len(chunks)} chunks")

    return chunks

def summarize_chunk(index, chunk):
    chunk_str = "\n".join(chunk)
    prompt = f"""The following is a section of the transcript of a youtube video. It is section #{index+1}:
    {chunk_str}
    Briefly summarize this section of the transcript in 100 characters or less."""

    if diagnostics:
        for line in prompt.split('\n'):
            print(f"# {line}")

    co= cohere.Client(user_secret)
    response = co.generate(
                model='xlarge',
                #model='command-beta',
                prompt= prompt,
                max_tokens=500,
                temperature=1.8,
                k=0,
                p=0.65,
                frequency_penalty=0.15,
                presence_penalty=0.15,
                stop_sequences=[],
                return_likelihoods='NONE')
    text_response = response.generations[0].text.strip()
    text_response = re.sub('\s+', ' ', text_response)
    filename = '%s_logs.txt' % time()
    with open('response_logs/%s' % filename, 'w') as outfile:
        outfile.write('PROMPT:\n\n' + prompt + '\n\n==========\n\nRESPONSE:\n\n' + text_response)
    with open('response.txt', 'w') as f:
        f.write(text_response)
    
    if diagnostics:
        print(f"# Response: {text_response}")
    
    return text_response


def summarize_the_summaries(summaries):
    max_retry = 5
    retry = 0
    summaries_str = ""
    for index, summary in enumerate(summaries):
        summaries_str += f"Summary of chunk {index+1}:\n{summary}\n\n"

    prompt = f"""The following are summaries of a youtube video in 5 minute chunks:"
    {summaries_str}
    Summarize the summaries."""

    # prompt = prompt.encode(encoding='ASCII',errors='ignore').decode()

    if diagnostics:
        for line in prompt.split('\n'):
            print(f"# {line}")

    while True:
        try:
            co= cohere.Client(user_secret)
            response = co.generate(
                model='xlarge',
                #model='command-beta',
                prompt= prompt,
                max_tokens=500,
                temperature=1.8,
                k=0,
                p=0.65,
                frequency_penalty=0.15,
                presence_penalty=0.15,
                stop_sequences=[],
                return_likelihoods='NONE')
            text_response_overall = response.generations[0].text.strip()
            text_response_overall = re.sub('\s+', ' ', text_response_overall)
            filename = '%s_log.txt' % time()
            with open('response_logs/%s' % filename, 'w') as outfile:
                outfile.write('PROMPT:\n\n' + prompt + '\n\n==========\n\nRESPONSE:\n\n' + text_response_overall)
            with open('response.txt', 'w') as f:
                f.write(text_response_overall)
            return text_response_overall
        except Exception as oops:
            retry += 1
            if retry >= max_retry:
                return "error: %s" % oops
            print('Error communicating with Cohere:', oops)
            sleep(1)

    if diagnostics:
        print(f"# Response: {text_response_overall}")

    return text_response_overall

def summarization_video(youtube_link):
  
  #video_id_or_url = sys.argv[1]
  video_id_or_url =  youtube_link

  # if the video id or url is a url, extract the video id
  video_id = get_video_id_from_video_id_or_url(video_id_or_url)

  if len(sys.argv) > 2:
      for arg in sys.argv[2:]:
          if arg == "--diagnostics":
              global diagnostics
              diagnostics = True

          if arg == "--mentions":
              global include_mentions
              include_mentions = True

  # chunks = get_chunks(transcript_file_name)
  chunks = get_chunks_from_youtube(video_id)

  if len(chunks) == 0:
      print("No chunks found")
      summaries = []
      summary_of_summaries= []
      return summaries, summary_of_summaries
  elif len(chunks) == 1:
      summary = summarize_chunk(0, chunks[0])
      print(f"\nSummary: {summary}")
      summaries = summary
      summary_of_summaries= []
      return summaries, summary_of_summaries

  else:
      # summarize each chunk
      summaries = []
      for index, chunk in enumerate(chunks):
          summary = summarize_chunk(index, chunk)
          summaries.append(summary)
          print(f"\nSummary of chunk {index+1}: {summary}")

      # summarize the chunk summaries 
      summary_of_summaries = summarize_the_summaries(summaries)

      print(f"\nSummary of summaries: {summary_of_summaries}")
      return summaries, summary_of_summaries


data_summarization = []
mp4_video = ''
audio_file = ''
diagnostics = 0
include_mentions = 0
summaries = []
summary_of_summaries= []

# Sidebar
with st.sidebar:
    user_secret = st.text_input(label = ":red[Cohere API key]",
                                placeholder = "Paste your Cohere API key",
                                type = "password")
    youtube_link = st.text_input(label = ":red[Youtube link]",
                                placeholder = "")
    if youtube_link and user_secret:
        youtube_video = YouTube(youtube_link)
        streams = youtube_video.streams.filter(only_audio=True)
        stream = streams.first()
        if st.button("Start Analysis"):
            if os.path.exists("summarization.csv"):
                os.remove("summarization.csv")
                
            with st.spinner('Running process...'):
                # Get the video mp4
                mp4_video = stream.download(filename='youtube_video.mp4')
                audio_file = open(mp4_video, 'rb')
                st.write(youtube_video.title)
                st.video(youtube_link) 


                # Summary
                summaries, summary_of_summaries = summarization_video(youtube_link)
                summarization = {
                    "title": youtube_video.title.strip(),
                    "summarizations of video in 5mins chunks": summaries,
                    "overall summary": summary_of_summaries
                }
                data_summarization.append(summarization)
                pd.DataFrame(data_summarization).to_csv('summarization.csv')
                st.success('Video summarized! Check out the Summary Tab')

st.title("Youtube Summarizer Using Cohere API ")
tab1, tab2 = st.tabs(["Intro", "Video Summary"])
with tab1:
    st.markdown('A simple app that uses Cohere\'s models to summarize a youtube video, without having to watch the video. ')
    st.markdown("""---""")
    st.write('***What this app does:***')
    st.checkbox('Visualize/play the video in the app.', value=True, disabled=True, label_visibility="visible")
    st.markdown("""---""")
    st.write('***Progress and features:***')
    st.checkbox('Play the youtube video within app.', value=True, disabled=True, label_visibility="visible")
    st.checkbox('Build a quick/simple app using streamlit.', value=True, disabled=True, label_visibility="visible")
    st.checkbox('Alternative option: run streamlit app in colab.', value=True, disabled=True, label_visibility="visible")
    st.checkbox('Multi-language integration: non-English videos compatibility.', value=False, disabled=True, label_visibility="visible")
    st.checkbox('Multi-language integration: allow users to ask questions in their languages.', value=False, disabled=True, label_visibility="visible")
    st.markdown("""---""")
    st.write('***Main tools used:***')
    st.write("- Cohere's X-Large model.")
    st.write("- Streamlit")
    st.markdown("""---""")
    st.write('Repo: [Github](https://github.com/ejri/youtube_summarizer_cohere)')

with tab2:    
    st.header("Video Summary:")
    if os.path.exists("summarization.csv"):
        df = pd.read_csv('summarization.csv')
        st.write(df)
