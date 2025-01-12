import json
import re
from datetime import datetime
from typing import List, Union, Dict, Optional

import flask
import requests
from flask import jsonify, render_template, request
from requests import Response

from data_management.app_db.app_data_db import app_db
from data_management.data_models.config.endpoints import LargeLanguageModelEndpoints
from data_management.data_models.data_classes.conversation import Conversation
from data_management.data_models.data_classes.persona import Persona
from log.logger import logger
from web_apps.base_class.web_app import FlaskDrivenWebApp


class FlaskBackEndApp(FlaskDrivenWebApp):
    def __init__(
            self,
            host: str = '0.0.0.0',
            port: int = 5000,
            llm_host: str = 'localhost',
            llm_port: int = 1234,
            llm_version_str: str = 'v1',
            debug: bool = False,
    ):
        super().__init__(
                host=host,
                port=port,
                debug=debug,
                enable_session=False,
                enable_socketio=True
        )
        self._llm_host = llm_host
        self._llm_port = llm_port
        self._llm_version_str = llm_version_str
        self._llm_endpoints = LargeLanguageModelEndpoints(
                base_url=self._llm_host,
                port=self._llm_port,
                version_str=self._llm_version_str,
        )
    
    def _associate_routes(self):
        self._app.add_url_rule('/', 'index', self._flask_serve_route_index_get, methods=['GET'])
        self._app.add_url_rule('/', 'llm', self._flask_serve_route_index, methods=['POST'])
        self._app.add_url_rule('/session', 'session', self._flask_serve_route_index, methods=['POST'])
        self._app.add_url_rule('/persona', 'persona', self._flask_serve_route_persona, methods=['POST'])
        
    @staticmethod
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
    
    def _flask_serve_route_index_get(self):
        # populate a page outlining the endpoints and their usage
        if self._debug:
            self.show_request()
        data = request.get_json()
        return jsonify({})
    
    def _flask_serve_route_index(self):
        # llm communication endpoint
        if self._debug:
            self.show_request()
        data = request.get_json()
        action_type = data['action_type']
        action_funcs = dict()
        if action_type not in action_funcs.keys():
            return jsonify({'error': 'Invalid request'}), 400
        result = action_funcs[action_type](data)
        return jsonify(result)
    
    def _flask_serve_route_persona(self):
        # persona creation/update/deletion endpoint
        if self._debug:
            self.show_request()
        data = request.get_json() # type: Dict[str, str]
        action_type = data['action_type']
        action_funcs = {
                'list':self.list_personas,
                'upsert':self.create_persona,
                'select':self.set_persona,
                'delete':self.delete_persona,
        }
        if action_type not in action_funcs.keys():
            return jsonify({'error':'Invalid request'}), 400
        result = action_funcs[action_type](data)
        return jsonify(result)
    
    def _flask_serve_route_session(self):
        # session history / settings endpoint user persistence
        if self._debug:
            self.show_request()
        data = request.get_json()
        action_type = data['action_type']
        action_funcs = dict()
        if action_type not in action_funcs.keys():
            return jsonify({'error': 'Invalid request'}), 400
        result = action_funcs[action_type](data)
        return jsonify(result)

    def get_model_list(self) -> Union[List[str], Response]:
        models_path = self._llm_endpoints.models
        endpoint_response = models_path.get()
        if endpoint_response.status_code == 200:
            models = endpoint_response.json()
        else:
            return jsonify({
                    "error": f"Failed to fetch models: {endpoint_response.status_code} - {endpoint_response.text}"})
        results = []
        for item in models['data']:
            results.append(item['id'])
        return results

    def list_models(self):
        model_list = self.get_model_list()
        return jsonify(model_list)


    def submit(self):
        session_id = self.check_session()
        conv_hist = app_db.get_conversation_history(session_id=session_id, persona_name='FeyCreature')
        llm_endpoints: LargeLanguageModelEndpoints = globals()['llm_endpoints']
        data = request.get_json()
        logger.info(f"FORM DATA RECEIVED:\n{data}\n")
        
        if not app_db.contains_persona('FeyCreature'):
            from data_management.app_db.init_db import init_db
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
        user_conv_item = Conversation(session_id=session_id, persona_name='FeyCreature',
                message_time=user_timestamp, conversation_sender='user',
                conversation_content=chat_input)
        app_db.upsert_conversation_entry(user_conv_item)
        payload = {"model": selected_model, "messages": [{"role": "system", "content": system_prompt},
                {"role": "user", "content": chat_input}], "temperature": 0.7, "max_tokens": -1,
                "stream": True}
        
        persona_timestamp = datetime.now()
        persona_conversation_item = Conversation(session_id=session_id, persona_name='FeyCreature',
                message_time=user_timestamp, conversation_sender='llm', conversation_content='')
        
        def generate_response() -> str:
            try:
                generated_response = llm_endpoints.chat_completions.post(headers=headers, json=payload,
                        stream=True)
            except requests.exceptions.RequestException as e:
                logger.error(f"Error during streaming: {e}")
                yield json.dumps({'role_name': 'system',
                        'text_content': f"An error occurred during the stream: {str(e)}",
                        'streaming_complete': True})
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
                                yield json.dumps({'role_name': '', 'text_content': '',
                                        'streaming_complete': True})
                            else:
                                role_name = delta['role']
                                content_text = delta['content']
                                yield json.dumps({'role_name': f'{role_name[0].upper()}{role_name[1:]}',
                                        'text_content': content_text,
                                        'streaming_complete': finish_reason is not None})
                        
                        except json.JSONDecodeError as e:
                            logger.error(
                                f"JSON Decode Error for chunk: {raw_response_data} exception: {e}")
            else:
                yield json.dumps({'role_name': 'system',
                        'text_content': f"Failed to send data: {generated_response.status_code} - {generated_response.text}"})
        
        generated_response = generate_response()
        persona_conversation_item.conversation_content = (
                f'{persona_conversation_item.conversation_content}{generated_response}')
        app_db.upsert_conversation_entry(persona_conversation_item)
        response = flask.Response(generated_response, mimetype='application/json',
                content_type='application/json')
        return response
    
    
    
    def create_persona(self):
        data = request.get_json()
        session_id = data['session_id']
        name = data['name']
        default_model = data['model']
        system_prompt = data['prompt']
        persona_data = Persona(name=name, default_model=default_model, system_prompt=system_prompt)
        print(persona_data)
        app_db.upsert_persona(persona_data)
    
    
    
    def set_persona(self):
        global CURRENT_PERSONA
        
        data = request.get_json()
        selected_persona = data.get('persona')
        
        if not selected_persona:
            return jsonify({"error": "Persona not provided"}), 400
        
        if not app_db.contains_persona(selected_persona):
            return jsonify({"error": f"Persona '{selected_persona}' does not exist"}), 404
        
        persona_details = app_db.fetch_persona(selected_persona)
        if not persona_details:
            return jsonify(
                    {"error": f"Failed to retrieve details for persona '{selected_persona}'"}), 500
        
        CURRENT_PERSONA = selected_persona
        
        return jsonify({"message": f"Persona set to '{selected_persona}'",
                "details": {"model": persona_details.default_model,
                        "prompt": persona_details.system_prompt}})
    
    
    
    def list_personas(self):
        def dictify(personas: List[Persona]):
            return {p.name: {'model': p.default_model, 'prompt': p.system_prompt} for p in personas}
        
        if not app_db.contains_persona('FeyCreature'):
            from data_management.app_db.init_db import init_db
            init_db()
        
        personas = app_db.get_personas()
        persona_dict = dictify(personas)
        
        # Add static personas
        persona_dict['System'] = {'model': 'system_model', 'prompt': 'You are in system debug mode.'}
        persona_dict['Helper'] = {'model': 'helper_model',
                'prompt': 'You are a helpful assistant who specializes in Dungeons & Dragons information.'}
        
        return jsonify(persona_dict)
    
    def delete_persona(self):
        ...