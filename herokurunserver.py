"""
This script runs the application for Heroku.
"""

import os
from PalrWebService import app
from flask_socketio import SocketIO

socketio = SocketIO(app)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app)
