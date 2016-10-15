from flask import Flask, jsonify, request
from flask_pymongo import PyMongo

app = Flask(__name__)

# connect to local database
app.config['MONGO_HOST'] = 'localhost'
app.config['MONGO_PORT'] = 27017
app.config['MONGO_DBNAME'] = 'local'
mongo = PyMongo(app, config_prefix='MONGO')
#mongo =  PyMongo(app)

@app.route("/users")
def list_users():
    users = mongo.db.users.find()
    i = 0
    for document in users:
        i+=1
        print i
        print(document)
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
