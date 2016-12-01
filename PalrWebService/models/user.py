""" Flask and other extensions instantiated here. """

from datetime import datetime
from mongokit import Document, Connection
from config import Config
from extensions import db

@db.register
class User(Document): 
    __database__ = Config.DatabaseConfig.MONGO_DBNAME
    __collection__ = 'users'

    structure = {
        '_id': basestring,
        'name': basestring,
        'password': basestring,
        'email' : basestring, 
        'country' : basestring, 
        "in_match_process": bool, 
        'is_temporarily_matched': bool,
        'is_permanently_matched': bool,
        'matched_with': list,
        'image_url': basestring,
        'in_match_process': bool
    }

    use_dot_notation = True
