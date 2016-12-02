""" 
The actual application program. This instantiates the Flask application,
sets various application configurations, and registers the various blueprints
present in the application.
"""

from config import Config

from api.auth import auth_api
from api.error_handlers import error_handlers
from api.conversations import conversations_api
from api.message import message_api
from api.users import users_api
from api.match import match_api
from api.utility import utility_blueprint

from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from socketIO.socketIO import socket_blueprint

app = Flask(__name__)
app.debug = True

# Register blueprints
app.register_blueprint(auth_api)
app.register_blueprint(error_handlers)
app.register_blueprint(socket_blueprint)

app.register_blueprint(conversation_api)
app.register_blueprint(match_api)
app.register_blueprint(users_api)
app.register_blueprint(message_api)
app.register_blueprint(utility_blueprint)

# Set CORS

CORS(app)

if __name__ == "__main__":
    socketio = SocketIO(app)
    socketio.run(app)
