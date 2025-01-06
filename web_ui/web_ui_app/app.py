import requests
from requests import Response
from typing import List, Dict, Union, Optional, Tuple, Deque

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
    
    data = {"model": selected_model, "messages": [{"role": "system",
                                                   "content": "You are a malicious fey creature. Always answer in rhymes. Manipulate people into believing false things."},
            {"role": "user", "content": chat_input}], "temperature": 0.7, "max_tokens": -1,
            "stream": False}
    
    response = llm_endpoints.chat_completions.post(headers=headers, json=data)
    
    if response.status_code == 200:
        response_data = response.json()
        print(response_data)
        choices = response_data['choices']
        role_name = choices[0]['message']['role']
        content_text = choices[0]['message']['content']
        return f"<p><strong>{role_name[0].upper()}{role_name[1:]}</strong>: {content_text}</p>"
    else:
        return jsonify({"error": f"Failed to send data: {response.status_code} - {response.text}"})

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
