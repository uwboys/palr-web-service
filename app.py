from flask import Flask
from flask_pymongo import PyMongo

app = Flask(__name__)
# connect to local database
app.config['MONGO_HOST'] = 'localhost'
app.config['MONGO_PORT'] = 27017
app.config['MONGO_DBNAME'] = 'local'
mongo = PyMongo(app, config_prefix='MONGO')
#mongo =  PyMongo(app)

@app.route("/")
def hello():
    return "Hello World!"


@app.route("/users")
def list_users():
    users = mongo.db.users.find()
    for document in users:
        print(document)
    print users
    return "Hello World!"

if __name__ == "__main__":
    app.run()
