from datetime import datetime
from mongokit import Document, Connection
from config import DatabaseConfig
import setup

@setup.mongoConnection.register
class User(Document): 
    __database__ = DatabaseConfig.MONGO_DBNAME
    __collection__ = 'messages'

    structure = {
        '_id': basestring,
        'name': basestring,
        'is_temporary_matched': bool,
        'is_permanently_matched': bool,
        'email': basestring,
        'location': basestring,
        'password': basestring,
        'in_match_process': bool
    }
