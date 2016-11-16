from datetime import datetime
from mongokit import Document, Connection
from config import DatabaseConfig
from setup import mongoConnection

@mongoConnection.register
class Message(Document): 
    __database__ = DatabaseConfig.MONGO_DBNAME
    __collection__ = 'messages'

    structure = {
        '_id': basestring,
        'content': basestring,
        'created_at': datetime,
        'conversation_data_id': basestring,
        'created_by': basestring
    }
