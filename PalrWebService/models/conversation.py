from datetime import datetime
from mongokit import Document, Connection
from config import Config 
from extensions import db

@db.register
class Conversation(Document): 
    __database__ = Config.DatabaseConfig.MONGO_DBNAME
    __collection__ = 'conversations'

    structure = {
        '_id': basestring,
        'created_at': datetime,
        'conversation_data_id': basestring,
        'user': basestring,
        'pal': basestring,
        'last_message_date': datetime,
        'request_permanent': bool,
        'is_permanent': bool 
    }
