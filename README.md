<h1 align="center">
Youtube Summarizer using Cohere API 
</h1>


# Youtube Video Summarizer Using Cohere API

A simple app that uses Cohere's models to summarize a youtube video.

This app summarizes long youtube videos into a few sentences using Cohere API. The video transcripts are chunked into 5min intervals, and summarized.
Then the summaries are compiled into a summary of the video.


### to do:

- [x] Integrate cohere API (X-Large Model)
- [x] Visualize/play the video in the app. 
- [x] Any English video [with english transcriptions]
- [x] Alternative option: run streamlit app in colab
- [x] Build a quick/simple app using streamlit
- [ ] Semantic search with embedding
- [ ] Sentiment analysis of the video content
- [ ] Graphs, graphs, and graphs about some of the stuff above.


# Running Locally

1. Clone the repo

```bash
git clone https://github.com/ejri/youtube_summarizer_cohere
cd youtube_summarizer_cohere
```
2. Install dependencies

These dependencies are required to install with the requirements.txt file:

``` bash
pip install -r requirements.txt
```

3. Run the Streamlit server

```bash
streamlit run app.py
```

# Running on Google Colab

1. Clone the repository

```
!git clone https://github.com/ejri/youtube_summarizer_cohere
%cd youtube_summarizer_cohere
```
2. Install dependencies

These dependencies are required to install with the requirements.txt file:

``` 
!pip install -r requirements.txt
```

3. Set up enviroment on colab:

if not installed already: 
```
!pip install pyngrok==5.2.1
```

Setup streamlit and ngrok
```
!streamlit run /content/youtube_summarizer_cohere/app.py &>/dev/null&
```

Create an account on ngrok, and paste your authenication token ----
```
!ngrok authtoken ----
```

making sure it's the correct version on the colab servers
```
#!wget https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-amd64.zip
!unzip /content/youtube_summarizer_cohere/ngrok-stable-linux-amd64.zip
```

Setting the server to accept running ngrok
```
get_ipython().system_raw('./ngrok http 8501 &')
```

Runs ngrok as localhost
```
! curl -s http://localhost:4040/api/tunnels | python3 -c \
    "import sys, json; print(json.load(sys.stdin)['tunnels'][0]['public_url'])"
```

4. Run the Streamlit server

```
!streamlit run /content/youtube_summarizer_cohere/app.py
```

# Run locally from CLI

1. Clone the repo

```bash
git clone https://github.com/ejri/youtube_summarizer_cohere
cd youtube_summarizer_cohere
```
2. Install dependencies

These dependencies are required to install with the requirements.txt file:

``` bash
pip install -r requirements.txt
```

3. Run the Streamlit server

```bash
python3 summarize_youtube_cli.py <link to youtube video>
```

references:
https://medium.com/@greyboi/summarize-youtube-with-text-davinci-003-fa4d182cc531
