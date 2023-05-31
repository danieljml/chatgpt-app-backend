import json
from flask import Flask, request
from flask_cors import CORS
from http import HTTPStatus

from csv_utils import split_csv
from openia.http_client import create_chat_completion, get_models, build_message
from openia.utils import get_content_from_successful_chat_response

app = Flask(__name__)
CORS(app)


def create_success_response(message):
    return {'response': {'message': message}}


def create_error_response(message, **kwargs):
    return {'error': {'message': message, **kwargs}}


@app.post('/validate_credentials/')
def validate_credentials():
    api_key = request.headers.get('Authorization')
    if api_key is None:
        return create_error_response('Field "Authorization" was expected but it was not found in the request headers'), HTTPStatus.BAD_REQUEST.value
    models = get_models(api_key)
    if not models.ok:
        error_message = models.json().get('error', {}).get('message', 'The error could not be identified')
        return create_error_response(error_message), models.status_code
    return create_success_response('The API key providad is valid'), HTTPStatus.OK.value


@app.post('/analyze_document/')
def analyze_document():
    api_key = request.headers.get('Authorization')
    if 'document' not in request.files:
        return create_error_response('Field "document" was expected but it was not found in the request body'), HTTPStatus.BAD_REQUEST.value
    document = request.files['document']
    document_content = document.stream.read().decode('utf-8')
    csvs = split_csv(document_content)
    messages = []
    for csv in csvs:
        response = create_chat_completion(api_key, [
            build_message('Interpret the following CSV and provide a summary highlighting interesting insights, avoid starting the message with something like "This data set this" or "These records are" since I am reusing the response and I want to be able to concatenate your different responses'),
            build_message(csv)
        ])
        response_content = response.json()
        if response.ok and response_content['choices']:
            messages += [get_content_from_successful_chat_response(response_content)]
    header = document_content.split('\n')[0]
    follow_up_response = create_chat_completion(api_key, [
        build_message('Interpret the following list of CSV headers and provide an extended summary, then a list of 10 suggestions for further analysis'),
        build_message(header)
    ])
    if follow_up_response.ok:
        messages += [get_content_from_successful_chat_response(follow_up_response.json())]
    return create_success_response('\n'.join(messages)) if messages else (create_error_response('The API could not generate a response for this content'), 400)
