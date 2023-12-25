import openai
import os
import logging
from dotenv import load_dotenv
from flask import Flask, request, Response, stream_with_context
from flask_cors import CORS
from flask_socketio import SocketIO
import weaviate
import json

from gouvx_pipeline import ask_gouvx

load_dotenv()

OPENAI_KEY = os.getenv("OPENAI_KEY")
WEAVIATE_ENDPOINT = os.getenv('WEAVIATE_ENDPOINT')
WEAVIATE_KEY = os.getenv('WEAVIATE_KEY')
HUGGINGFACE_KEY = os.getenv('HUGGINGFACE_KEY')
PORT = os.getenv('PORT', '8888')

WEAVIATE_NRESULTS = int(os.getenv('WEAVIATE_NRESULTS', '1'))

app = Flask(__name__)
CORS(app)

openai.api_key = OPENAI_KEY
logging.info("api key passed to openAI")


client = weaviate.Client(
    url = WEAVIATE_ENDPOINT,
    auth_client_secret=weaviate.AuthApiKey(api_key=WEAVIATE_KEY),
    additional_headers={
        'X-HuggingFace-Api-Key': HUGGINGFACE_KEY
    }
  )


@app.route('/', methods=['GET'])
def main():
    return "L'API GouvX est prête a être appellée"


@app.route('/ask/', methods=['POST'])
def ask():
    prompt = request.form['question']
    sources = request.form['sources']
    history = request.form['history']

    history = json.loads(history)

    print("user:", request.remote_addr, "prompt:", prompt, "sources:", sources)

    try:
        if len(history) > 10:
            raise ValueError("conversation too long")
        query_results, chatgpt_generator = ask_gouvx(prompt, client=client, model=None, n_results=WEAVIATE_NRESULTS, history=history, sources=sources)
    except ValueError:
        query_results = None
        chatgpt_generator = (lambda _: "Désolé j'ai atteint mon quota de réponses pour le moment")("")

    def response_stream(chatgpt_generator, query_results=None):
        if query_results:
            yield json.dumps(query_results).encode('utf-8')
        else:
            yield json.dumps([]).encode('utf-8')       
        
        yield "\n".encode('utf-8')

        for line in chatgpt_generator:
            yield line.encode('utf-8')

    return Response(stream_with_context(response_stream(chatgpt_generator, query_results)), mimetype='text/plain', direct_passthrough=True)
