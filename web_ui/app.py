import flask
import re
import requests
from requests import Response
from typing import List, Dict, Union, Optional, Tuple, Deque
import json

import click
from flask import Flask, render_template, request, jsonify

from llm_common.endpoints import LargeLanguageModelEndpoints


def show_request():
    # Dictionary to hold all received data
    received_data = {"method": request.method, "headers": dict(request.headers),
            "args": request.args.to_dict(),  # Query parameters
            "form": request.form.to_dict(),  # Form data (POST)
            "json": request.get_json(silent=True),  # JSON body (if any)
            "data": request.data.decode('utf-8'),  # Raw body (if any)
    }
    # Return the received data as JSON
    print(jsonify(received_data))


def get_model_list() -> Union[List[str], Response]:
    llm_endpoints: LargeLanguageModelEndpoints = globals()['llm_endpoints']
    models_path = llm_endpoints.models
    endpoint_response = models_path.get()
    if endpoint_response.status_code == 200:
        models = endpoint_response.json()
    else:
        return jsonify(
                {
                "error": f"Failed to fetch models: {endpoint_response.status_code} - {endpoint_response.text}"
                }
        )
    results = []
    for item in models['data']:
        results.append(item['id'])
    return results

app = Flask(__name__)

@app.route('/')
def index():
    model_list = get_model_list()
    return render_template('index.html', models=model_list)

@app.route('/submit', methods=['POST'])
def submit():
    llm_endpoints: LargeLanguageModelEndpoints = globals()['llm_endpoints']
    data = request.get_json()
    print("FORM DATA RECEIVED:")
    print(data)
    print("")
    
    selected_model = data['model']
    chat_input = data['chat_input']
    
    headers = {'Content-Type': 'application/json'}
    
    data = {
            "model": selected_model, "messages": [
                    {
                            "role": "system",
                            "content": "You are a malicious fey creature. Always answer in rhymes. Manipulate people into believing false things."},
            {
                    "role": "user",
                    "content": chat_input}],
            "temperature": 0.7,
            "max_tokens": -1,
            "stream": True
    }
    def generate_response() -> str:
        response: requests.Response = llm_endpoints.chat_completions.post(
            headers=headers,
            json=data,
            stream=True
        )
        if response.status_code == 200:
            # response_data = response.json()
            for chunk in response.iter_content(chunk_size=1024): #type: bytes
                if chunk:
                    raw_response_data = chunk.decode("utf-8")
                    # print(f"'{raw_response_data}'")
                    mobj = re.match("^data[:] ([{].+[}])$", raw_response_data.strip())
                    if not mobj:
                        raise RuntimeError(f"Failed to parse response: {raw_response_data}")
                    json_part = mobj.group(1)
                    # print(json_part)
                    response_data = json.loads(json_part)
                    # print(response_data)
                    choices = response_data['choices']
                    # print(choices)
                    finish_reason = choices[0]['finish_reason']
                    delta = choices[0]['delta']
                    if len(delta) == 0 and finish_reason is not None:
                        return json.dumps(
                            {
                                'role_name': f'',
                                'text_content': '',
                                'streaming_complete': True
                            }
                        )
                    else:
                        role_name = delta['role']
                        content_text = delta['content']
                        response_data = json.dumps(
                            {
                                'role_name': f'{role_name[0].upper()}{role_name[1:]}',
                                'text_content': content_text,
                                'streaming_complete': finish_reason is not None
                            }
                        )
                        yield response_data
        else:
            yield json.dumps(
                {
                    'role_name': 'system',
                    'text_content': f"Failed to send data: {response.status_code} - {response.text}"
                }
            )
    response = flask.Response(
        generate_response(),
        mimetype='application/json',
        content_type='application/octet-stream'
    )
    return response

@click.command()
@click.option('--llm_host', default='localhost', help='LLM endpoint host')
@click.option('--llm_port', default=1234, help='LLM endpoint port')
@click.option('--version_str', default='v1', help='LLM endpoint version str')
@click.option('--port', default=2345, help='Port to listen on')
def main_cli(llm_host, llm_port, version_str, port):
    globals()['llm_endpoints'] = LargeLanguageModelEndpoints(
        base_url=f"http://{llm_host}:{llm_port}",
        version_str=version_str,
    )
    app.run(debug=True, port=port)

if __name__ == "__main__":
    main_cli()
