import cohere
import sys
from youtube_transcript_api import YouTubeTranscriptApi
from time import time,sleep
import re

diagnostics = 0
include_mentions = 0


def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return infile.read()

def save_file(filepath, content):
    with open(filepath, 'w', encoding='utf-8') as outfile:
        outfile.write(content)

co= cohere.Client(open_file('/content/cohereapikey.txt'))

def get_video_id_from_video_id_or_url(video_id_or_url):
    # fetch the video ID from the URL. if it's more that 11 characters long, crop it to make it 11. 
    if len(video_id_or_url) > 11:
        return video_id_or_url[-11:]
    else:
        return video_id_or_url

def get_chunks_from_youtube(video_id):
    # fetch video's transcript
    # and chunk it into several 5min intervals
    transcript = YouTubeTranscriptApi.get_transcript(video_id)

    chunks = []

    start_timestamp = 0.0
    current_timestamp_mins = 0.0

    current_chunk = []

    for entry in transcript:
        current_timestamp_mins = entry['start'] / 60.0

        # chunk at 5 minutes intervals
        if current_timestamp_mins - start_timestamp > 5:
            # add current chunk to a list of chunks
            chunks.append(current_chunk)
            # then reset the start timestamp
            start_timestamp = current_timestamp_mins
            # reset current chunk
            current_chunk = []

        # append the chunk's text
        current_chunk.append(entry['text'])

    # the last chunk of the video
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

    
    response = co.generate(
                model='xlarge',
                # model='command-beta',
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
            response = co.generate(
                model='xlarge',
                # model='command-beta',
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
            filename = '%s_log.txt' % time()
            with open('response_logs/%s' % filename, 'w') as outfile:
                outfile.write('PROMPT:\n\n' + prompt + '\n\n==========\n\nRESPONSE:\n\n' + text_response)
            with open('response.txt', 'w') as f:
                f.write(text_response)
            return text_response
        except Exception as oops:
            retry += 1
            if retry >= max_retry:
                return "error: %s" % oops
            print('Error communicating with Cohere:', oops)
            sleep(1)

    if diagnostics:
        print(f"# Response: {text_response}")

    return text_response

def main():
    # the video transcript
    if len(sys.argv) < 2:
        print("Usage: python3 sumvid.py <video id or url>")
        sys.exit(1)

    video_id_or_url = sys.argv[1]

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

    chunks = get_chunks_from_youtube(video_id)

    if len(chunks) == 0:
        print("No chunks found")
    elif len(chunks) == 1:
        summary = summarize_chunk(0, chunks[0])
        print(f"\nSummary: {summary}")

    else:
        # summarize each chunk
        summaries = []
        for index, chunk in enumerate(chunks):
            summary = summarize_chunk(index, chunk)
            summaries.append(summary)
            print(f"\nSummary of chunk {index+1}: {summary}")

        # compile the summaries
        summary_of_summaries = summarize_the_summaries(summaries)

        print(f"\nSummary of summaries: {summary_of_summaries}")

if __name__ == "__main__":
    main()