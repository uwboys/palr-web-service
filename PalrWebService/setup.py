from flask import Flask
from config import Config, DatabaseConfig
from api.auth import auth_api
from api.conversations import conversation_api
from api.match import match_api
from api.users import users_api
from api.message import message_api
from flask_mongokit import Connection

app = Flask(__name__)

app.config['SECRET_KEY'] = Config.SECRET_KEY

# Register blueprints

app.register_blueprint(auth_api)
app.register_blueprint(conversation_api)
app.register_blueprint(match_api)
app.register_blueprint(users_api)
app.register_blueprint(message_api)

# Establish database connection
mongoConnection = Connection(
        host=DatabaseConfig.MONGO_HOST, 
        port=DatabaseConfig.MONGO_PORT, 
    )

mongoConnection.palrdb.authenticate(
        name=DatabaseConfig.MONGO_USERNAME,
        password=DatabaseConfig.MONGO_PASSWORD
    )

