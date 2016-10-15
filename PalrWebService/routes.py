import pymongo
from flask import Flask, jsonify, request
from pymongo import MongoClient
from PalrWebService import app
MONGODB_URI = 'mongodb://admin:admin@ds044989.mlab.com:44989/palrdb'

# connect to local database
#app.config['MONGO_HOST'] = 'ds044989.mlab.com'
#app.config['MONGO_PORT'] = 44989
#app.config['MONGO_DBNAME'] = 'palrdb'
#mongo = PyMongo(app, config_prefix='MONGO')
#mongo =  PyMongo(app)
mongo = pymongo.MongoClient(MONGODB_URI)
db = mongo.get_default_database()

@app.route("/")
def testServer():
    return "Hello World!"


@app.route("/users")
def list_users():
    users = db['users']
    cursor = users.find()
    i = 0
    for document in cursor:
        i+=1
        print i
        print('Username = %s Password = %s' % (document['username'], document['password']))
    return "Hello World!"

@app.route('/login', methods=['POST'])
def login():
    json = request.get_json()
    print json
    return "hello"

@app.route('/register', methods = ['POST'])
def new_user():
    username = request.get_json().get('username')
    password = request.get_json().get('password')

    if username is None or password is None:
        abort(400) # missing arguments
    if User.query.filter_by(username = username).first() is not None:
        abort(400) # existing user

    user = User(username = username)
    user.hash_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({ 'username': user.username }), 201, {'Location': url_for('get_user', id = user.id, _external = True)}

if __name__ == "__main__":
    app.run()
