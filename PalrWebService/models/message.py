from datetime import datetime
from mongokit import Document, Connection
from config import Config
from extensions import db

@db.register
class Message(Document): 
    __database__ = Config.DatabaseConfig.MONGO_DBNAME
    __collection__ = 'messages'

    structure = {
        '_id': basestring,
        'content': basestring,
        'created_at': datetime,
        'conversation_data_id': basestring,
        'created_by': basestring
    }

    use_dot_notation = True
