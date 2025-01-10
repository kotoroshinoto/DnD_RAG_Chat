from datetime import datetime

import flask
import re
import requests
from requests import Response
from typing import List, Union
import json

import click
from flask import Flask, render_template, request, jsonify, session
from flask_session import Session
import uuid
from flask_sqlalchemy import SQLAlchemy


from llm_common.endpoints import  LargeLanguageModelEndpoints
from app_db.app_data_db import app_db
from llm_common.persona import Persona
from llm_common.conversation import Conversation
from log.logger import logger


# app_db = AppDataDB()
CURRENT_PERSONA = "helper"

app = Flask(__name__)

app.secret_key = 'your_secret_key'  # Required for sessions

# Set up SQLAlchemy for SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flask.db'
db = SQLAlchemy(app)

app.config['SESSION_TYPE'] = 'sqlalchemy'
app.config['SESSION_SQLALCHEMY'] = db  # SQLite session storage
app.config['SESSION_PERMANENT'] = False  # Set permanent session (optional)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
Session(app)

def show_request():
    # Dictionary to hold all received data
    received_data = {"method": request.method, "headers": dict(request.headers),
            "args": request.args.to_dict(),  # Query parameters
            "form": request.form.to_dict(),  # Form data (POST)
            "json": request.get_json(silent=True),  # JSON body (if any)
            "data": request.data.decode('utf-8'),  # Raw body (if any)
    }
    # Return the received data as JSON
    logger.info(jsonify(received_data))


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


def check_session() -> uuid.UUID:
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    logger.info(f"session id: {session['session_id']}")
    return session['session_id']

@app.route('/')
def index():
    session_id = check_session()
    model_list = get_model_list()
    conv_hist = app_db.get_conversation_history(
            session_id=session_id,
            persona_name='FeyCreature'
    )
    # use conv hist to pre-populate chat
    return render_template('index.html', models=model_list)

@app.route('/list_models')
def list_models():
    model_list = get_model_list()
    return jsonify(model_list)

@app.route('/submit', methods=['POST'])
def submit():
    session_id = check_session()
    conv_hist = app_db.get_conversation_history(
            session_id=session_id,
            persona_name='FeyCreature'
    )
    llm_endpoints: LargeLanguageModelEndpoints = globals()['llm_endpoints']
    data = request.get_json()
    logger.info(f"FORM DATA RECEIVED:\n{data}\n")

    if not app_db.contains_persona('FeyCreature'):
        from app_db.init_db import init_db
        init_db()
    
    selected_persona = globals().get('CURRENT_PERSONA', 'FeyCreature')
    logger.info(f"Using persona: {selected_persona}")
    
    if selected_persona == 'System':
        system_prompt = 'You are in system debug mode.'
    elif selected_persona == 'Helper':
        system_prompt = 'You are a helpful assistant who specializes in Dungeons & Dragons information.'
    else:
        persona_details = app_db.fetch_persona(selected_persona)
        system_prompt = persona_details.system_prompt if persona_details else "Default persona system prompt."
    
    selected_model = data['model']
    chat_input = data['chat_input']
    
    headers = {'Content-Type': 'application/json'}
    user_timestamp = datetime.now()
    user_conv_item = Conversation(
        session_id=session_id,
        persona_name='FeyCreature',
        message_time=user_timestamp,
        conversation_sender='user',
        conversation_content=chat_input
    )
    app_db.upsert_conversation_entry(user_conv_item)
    payload = {
            "model": selected_model, "messages": [
                {
                        "role": "system",
                        "content": system_prompt
                },
                {
                        "role": "user",
                        "content": chat_input
                }
            ],
            "temperature": 0.7,
            "max_tokens": -1,
            "stream": True
    }
    
    persona_timestamp = datetime.now()
    persona_conversation_item = Conversation(
        session_id=session_id,
        persona_name='FeyCreature',
        message_time=user_timestamp,
        conversation_sender='llm',
        conversation_content=''
    )
    def generate_response() -> str:
        try:
            generated_response = llm_endpoints.chat_completions.post(
                headers=headers,
                json=payload,
                stream=True
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Error during streaming: {e}")
            yield json.dumps({
                'role_name': 'system',
                'text_content': f"An error occurred during the stream: {str(e)}",
                'streaming_complete': True
            })
            return
        
        if generated_response.status_code == 200:
            for chunk in generated_response.iter_content(chunk_size=1024):
                if chunk:
                    raw_response_data = chunk.decode("utf-8")
                    mobj = re.match("^data[:] ([{].+[}])$", raw_response_data.strip())
                    if not mobj:
                        logger.error(f"Failed to parse generated_response: {raw_response_data}")
                        continue
                    
                    json_part = mobj.group(1)
                    try:
                        response_data = json.loads(json_part)
                        choices = response_data['choices']
                        finish_reason = choices[0]['finish_reason']
                        delta = choices[0]['delta']
                        
                        if len(delta) == 0 and finish_reason is not None:
                            yield json.dumps({
                                'role_name': '',
                                'text_content': '',
                                'streaming_complete': True
                            })
                        else:
                            role_name = delta['role']
                            content_text = delta['content']
                            yield json.dumps({
                                'role_name': f'{role_name[0].upper()}{role_name[1:]}',
                                'text_content': content_text,
                                'streaming_complete': finish_reason is not None
                            })
                    
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON Decode Error for chunk: {raw_response_data} exception: {e}")
        else:
            yield json.dumps(
                {
                    'role_name': 'system',
                    'text_content': f"Failed to send data: {generated_response.status_code} - {generated_response.text}"
                }
            )
    generated_response = generate_response()
    persona_conversation_item.conversation_content = (
            f'{persona_conversation_item.conversation_content}{generated_response}'
    )
    app_db.upsert_conversation_entry(persona_conversation_item)
    response = flask.Response(
        generated_response,
        mimetype='application/json',
        content_type='application/json'
    )
    return response


@app.route('/create_persona', methods=['POST'])
def create_persona():
    data = request.get_json()
    name = data['name']
    default_model = data['model']
    system_prompt = data['prompt']
    persona_data = Persona(name=name, default_model=default_model, system_prompt=system_prompt)
    print(persona_data)
    app_db.upsert_persona(persona_data)

@app.route('/persona', methods=['POST'])
def set_persona():
    global CURRENT_PERSONA

    data = request.get_json()
    selected_persona = data.get('persona')

    if not selected_persona:
        return jsonify({"error": "Persona not provided"}), 400

    if not app_db.contains_persona(selected_persona):
        return jsonify({"error": f"Persona '{selected_persona}' does not exist"}), 404

    persona_details = app_db.fetch_persona(selected_persona)
    if not persona_details:
        return jsonify({"error": f"Failed to retrieve details for persona '{selected_persona}'"}), 500

    CURRENT_PERSONA = selected_persona

    return jsonify({
        "message": f"Persona set to '{selected_persona}'",
        "details": {
            "model": persona_details.default_model,
            "prompt": persona_details.system_prompt
        }
    })


@app.route('/list_personas', methods=['GET'])
def list_personas():
    def dictify(personas: List[Persona]):
        return {
            p.name: {
                'model': p.default_model,
                'prompt': p.system_prompt
            }
            for p in personas
        }

    if not app_db.contains_persona('FeyCreature'):
        from app_db.init_db import init_db
        init_db()
    
    personas = app_db.get_personas()
    persona_dict = dictify(personas)

    # Add static personas
    persona_dict['System'] = {
        'model': 'system_model',
        'prompt': 'You are in system debug mode.'
    }
    persona_dict['Helper'] = {
        'model': 'helper_model',
        'prompt': 'You are a helpful assistant who specializes in Dungeons & Dragons information.'
    }

    return jsonify(persona_dict)



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
