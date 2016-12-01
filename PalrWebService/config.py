import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super-secret-key'

    class DatabaseConfig:
        MONGO_HOST = os.environ.get('MONGO_HOST') or 'ds044989.mlab.com'
        MONGO_PORT = os.environ.get('MONGO_PORT') or 44989
        MONGO_DBNAME = os.environ.get('MONGO_DBNAME') or 'palrdb'
        MONGO_USERNAME = os.environ.get('MONGO_USERNAME') or 'admin'
        MONGO_PASSWORD = os.environ.get('MONGO_PASSWORD') or 'admin'

    class SocketIOConfig:
        SOCKET_IO_NAMESPACE = '/ws'




