""" Flask and other extensions instantiated here. """

import logging

from config import Config
from logging import Formatter

from flask_mongokit import Connection

# Setup the logger
LOG = logging.getLogger(__name__)

handler = logging.StreamHandler()
handler.setFormatter(Formatter(
    '%(asctime)s %(levelname)s: %(message)s '
    '[in %(pathname)s:%(lineno)d]'
))

# Logging configuration parameters
LOG.addHandler(handler)
LOG.setLevel(logging.DEBUG)

 # Establish database connection
db = Connection(host=Config.DatabaseConfig.MONGO_HOST, port=Config.DatabaseConfig.MONGO_PORT)
db.palrdb.authenticate(name=Config.DatabaseConfig.MONGO_USERNAME, password=Config.DatabaseConfig.MONGO_PASSWORD)
