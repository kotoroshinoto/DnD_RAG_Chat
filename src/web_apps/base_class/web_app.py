import abc
from flask import Flask
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session


class FlaskDrivenWebApp(abc.ABC):
    def __init__(self, host: str = '0.0.0.0', port: int = 2345, debug: bool = False, enable_session: bool = False, enable_socketio: bool = False):
        self._host = host
        self._port = port
        self._debug = debug
        self._socketio = SocketIO()
        self._app = Flask(__name__)
        
        self._app.secret_key = 'your_secret_key'  # Required for sessions
        
        if enable_session:
            # Set up SQLAlchemy for SQLite
            self._app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flask.db'
            self._db = SQLAlchemy(self._app)
            
            self._app.config['SESSION_TYPE'] = 'sqlalchemy'
            self._app.config['SESSION_SQLALCHEMY'] = self._db  # SQLite session storage
            self._app.config['SESSION_PERMANENT'] = False  # Set permanent session (optional)
            self._app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
            Session(self._app)
            
        if enable_socketio:
            self._socketio.init_app(self._app)
            self._associate_socketio_events()
        
        self._associate_routes()
        
    
    def run(self):
        self._socketio.run(self._app, host=self._host, port=self._port, debug=self._debug)
    
    @abc.abstractmethod
    def _associate_routes(self):
        pass
    
    def _associate_socketio_events(self):
        #not every app will enable or define socketio events, so this method isn't abstract, but intentionally does nothing
        pass

__all__ = ['FlaskDrivenWebApp']
