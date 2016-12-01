""" 
The actual application program. This instantiates the Flask application,
sets various application configurations, and registers the various blueprints
present in the application.
"""

from config import Config

from api.auth import auth_api
from api.error_handlers import error_handlers

from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO, emit

from socket-io import socke

'''
from api.conversations import conversation_api
from api.match import match_api
from api.users import users_api
from api.message import message_api
'''

app = Flask(__name__)
app.debug = True

# Register blueprints
app.register_blueprint(auth_api)
app.register_blueprint(error_handlers)


'''
app.register_blueprint(conversation_api)
app.register_blueprint(match_api)
app.register_blueprint(users_api)
app.register_blueprint(message_api)
'''

# Set CORS

CORS(app)

if __name__ == "__main__":
    socketio.run(app)
