from flask import Flask, jsonify, request, Response, abort
from werkzeug.security import generate_password_hash, check_password_hash
from flask_pymongo import PyMongo
from models.user import User
from datetime import datetime, timedelta
import jwt
import pymongo
from pymongo import MongoClient

app = Flask(__name__)
MONGODB_URI = 'mongodb://admin:admin@ds044989.mlab.com:44989/palrdb'

app.config['SECRET_KEY'] = 'super-secret-key'

mongo = pymongo.MongoClient(MONGODB_URI)

@app.route("/", methods=['GET'])
def testServer():
    return "Hello World!"

def create_token(user_id):
    payload = {
            # subject
            'sub': user_id,
            #issued at
            'iat': datetime.utcnow(),
            #expiry
            'exp': datetime.utcnow() + timedelta(days=1)
            }

    token = jwt.encode(payload, app.secret_key, algorithm='HS256')
    return token.decode('unicode_escape')

def parse_token(req):
    token = req.headers.get('Authorization').split()[1]
    return jwt.decode(token, app.secret_key, algorithms='HS256')

@app.errorhandler(400)
def respond400(error):
    return jsonify({'message': error.description['message']})

@app.route("/users", methods=['GET'])
def list_users():
    cursor = mongo.db.users.find()
    i = 0
    for document in cursor:
        i+=1
        print i
        print('Username = %s Password = %s' % (document['username'], document['password']))
    return "Hello World!"

@app.route('/login', methods=['POST'])
def login():
    email = request.get_json().get('email')
    password = request.get_json().get('password')

    cursor = mongo.db.users.find({"email": email})

    if cursor.count() == 0:
        error_message = "A user with the email " + email + " does not exist."
        abort(400, {'message': error_message})


    user_document = cursor.next()

    if not check_password_hash(user_document['password'], password):
        error_message = "Invalid password for " + email + "."
        abort(400, {'message': error_message})

    userid = str(user_document['_id'])
    token = create_token(userid)
    print(token)
    resp = jsonify({"access_token": token,
        "userid": userid})

    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route('/register', methods = ['POST'])
def register():
    name = request.get_json().get('name')
    password = request.get_json().get('password')
    email = request.get_json().get('email')
    location = request.get_json().get('location')

    print request.get_json()

    if name is None or password is None or email is None:
        # missing arguments
        abort(400, {'message': 'Missing required parameters' \
                ' name, password, email, and location are ALL required.'})

        # Should do error checking to see if user exists already
    if mongo.db.users.find({"email": email}).count() > 0:
        # Email already exists
        abort(400, {'message': 'A user with the email #{email} already exists'})



    _id = mongo.db.users.insert({"name": name, "password": generate_password_hash(password), "email" : email, "location": location})
    print str(_id)

    user = User(str(_id), name, password, email, location)

    # Now we have the Id, we need to create a jwt access token
    # and send the corresponding response back
    token = create_token(user.id)
    print(token)
    resp = jsonify({"access_token": token,
        "userid": str(_id)})

    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

if __name__ == "__main__":
    app.run()
