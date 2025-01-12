import json
import re
import uuid
from datetime import datetime
from typing import List, Union

import flask
import requests
from flask import jsonify, render_template, request, session
from requests import Response

# from data_management.app_db.app_data_db import app_db
from data_management.data_models.config.endpoints import LargeLanguageModelEndpoints
from data_management.data_models.data_classes.conversation import Conversation
from data_management.data_models.data_classes.persona import Persona
from log.logger import logger
from web_apps.base_class.web_app import FlaskDrivenWebApp


class FlaskFrontEndApp(FlaskDrivenWebApp):
    def __init__(self, host:str='0.0.0.0', port:int=2345, debug:bool=False):
        super().__init__(
                host=host,
                port=port,
                debug=debug,
                enable_session=True,
                enable_socketio=True
        )
        
    #static methods
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
    
    @staticmethod
    def check_session() -> uuid.UUID:
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
        logger.info(f"session id: {session['session_id']}")
        return session['session_id']
    
    @staticmethod
    def get_model_list() -> Union[List[str], Response]:
        llm_endpoints: LargeLanguageModelEndpoints = globals()['llm_endpoints']
        models_path = llm_endpoints.models
        endpoint_response = models_path.get()
        if endpoint_response.status_code == 200:
            models = endpoint_response.json()
        else:
            return jsonify({"error": f"Failed to fetch models: {endpoint_response.status_code} - {endpoint_response.text}"})
        results = []
        for item in models['data']:
            results.append(item['id'])
        return results
    
    #flask stuff
    @staticmethod
    def _flask_serve_route_index():
        return render_template('index.html')
    
    def _associate_routes(self):
        self._app.add_url_rule('/', 'index', self.__class__._flask_serve_route_index)
    
    # socket stuff
    def _client_message_print(self, message: str, *args, **kwargs):
        session_id = self.check_session()
        print(f'client ({session_id}) sent: ' + str(message))
    
    def _client_requests_models(self, *args, **kwargs):
        model_list = self.__class__.get_model_list()
        print('sending:', model_list)
        self._socketio.emit('client receive models', model_list)
    
    def _client_requests_chat_history(self, *args, **kwargs):
        session_id = self.__class__.check_session()
        conv_hist = app_db.get_conversation_history(session_id=session_id,
                                                    persona_name='FeyCreature')
        # this doesn't work, need to convert to json format or something made of basic types,
        # or give the model a function that lets socketio work with it
        self._socketio.emit('client receive chat history', conv_hist.to_dict())
    
    def _client_request_persona_upsert(self, data: json, *args, **kwargs):
        session_id = self.check_session()
        name = data['name']
        default_model = data['model']
        system_prompt = data['prompt']
        persona_data = Persona(name=name, default_model=default_model, system_prompt=system_prompt)
        logger.debug(f"{session_id} requests creation/update of {persona_data}")
        app_db.upsert_persona(persona_data)
        logger.debug(f"{persona_data} creation/update completed")
    
    def _client_request_persona_delete(self, name: str, *args, **kwargs):
        session_id = self.check_session()
        logger.debug(f"{session_id} requests deletion of persona: {name}")
        
    def _client_request_persona_details(self, name: str, *args, **kwargs):
        session_id = self.check_session()
        logger.debug(f"{session_id} requests details of persona: {name}")
    
    def _client_request_persona_list(self, *args, **kwargs):
        session_id = self.check_session()
        logger.debug(f"{session_id} requests list of personas")
        
        if not app_db.contains_persona('FeyCreature'):
            from data_management.app_db.init_db import init_db
            init_db()
        
        personas = app_db.get_personas()
        persona_dict = {p.name: {'model': p.default_model, 'prompt': p.system_prompt} for p in personas}
        
        # Add static personas
        persona_dict['System'] = {'model': 'system_model', 'prompt': 'You are in system debug mode.'}
        persona_dict['Helper'] = {'model': 'helper_model', 'prompt': 'You are a helpful assistant who specializes in Dungeons & Dragons information.'}
        
        return jsonify(persona_dict)
    
    def _client_request_persona_set(self, name: str, *args, **kwargs):
        session_id = self.check_session()
        logger.debug(f"{session_id} has chosen to set their active persona to: {name}")
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
        
        return jsonify({"message": f"Persona set to '{selected_persona}'", "details": {"model": persona_details.default_model, "prompt": persona_details.system_prompt}})
    
    def _client_send_chat_to_llm(self, message ,*args, **kwargs):
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
        user_conv_item = Conversation(session_id=session_id, persona_name='FeyCreature', message_time=user_timestamp, conversation_sender='user', conversation_content=chat_input)
        app_db.upsert_conversation_entry(user_conv_item)
        payload = {"model": selected_model, "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": chat_input}], "temperature": 0.7,
                "max_tokens": -1, "stream": True}
        
        persona_timestamp = datetime.now()
        persona_conversation_item = Conversation(session_id=session_id, persona_name='FeyCreature', message_time=user_timestamp, conversation_sender='llm', conversation_content='')
        
        def generate_response() -> str:
            try:
                generated_response = llm_endpoints.chat_completions.post(headers=headers, json=payload, stream=True)
            except requests.exceptions.RequestException as e:
                logger.error(f"Error during streaming: {e}")
                yield json.dumps({'role_name': 'system', 'text_content': f"An error occurred during the stream: {str(e)}", 'streaming_complete': True})
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
                                yield json.dumps({'role_name': '', 'text_content': '', 'streaming_complete': True})
                            else:
                                role_name = delta['role']
                                content_text = delta['content']
                                yield json.dumps(
                                        {'role_name': f'{role_name[0].upper()}{role_name[1:]}', 'text_content': content_text, 'streaming_complete': finish_reason is not None})
                        
                        except json.JSONDecodeError as e:
                            logger.error(f"JSON Decode Error for chunk: {raw_response_data} exception: {e}")
            else:
                yield json.dumps({'role_name': 'system', 'text_content': f"Failed to send data: {generated_response.status_code} - {generated_response.text}"})
        
        generated_response = generate_response()
        persona_conversation_item.conversation_content = (f'{persona_conversation_item.conversation_content}{generated_response}')
        app_db.upsert_conversation_entry(persona_conversation_item)
        response = flask.Response(generated_response, mimetype='application/json', content_type='application/json')
        return response
        
    def _associate_socketio_events(self):
        self._socketio.on_event('client message print', self._client_message_print)
        self._socketio.on_event('client request models', self._client_requests_models)
        
        self._socketio.on_event('client request chat history', self._client_requests_chat_history)
        self._socketio.on_event('client send chat to llm', self._client_send_chat_to_llm)
        
        self._socketio.on_event('client request persona upsert', self._client_request_persona_upsert)
        self._socketio.on_event('client request persona delete', self._client_request_persona_delete)
        self._socketio.on_event('client request persona details', self._client_request_persona_details)
        self._socketio.on_event('client request persona set', self._client_request_persona_set)
        self._socketio.on_event('client request persona list', self._client_request_persona_list)
    
    def run(self):
        self._socketio.run(
                self._app,
                host=self._host,
                port=self._port,
                debug=self._debug,
        )
