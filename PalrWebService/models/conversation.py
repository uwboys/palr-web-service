from datetime import datetime
from mongokit import Document, Connection
from config import DatabaseConfig
from setup import mongoConnection

@mongoConnection.register
class Conversation(db.Document): 
    __collection__ = 'messages'
    __database__ = DatabaseConfig.MONGO_DBNAME

    structure = {
        '_id': basestring,
        'created_at': datetime,
        'conversation_data_id': basestring,
        'user': basestring,
        'pal': basestring,
        'last_message_date': datetime
    }
