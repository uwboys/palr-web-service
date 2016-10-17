from flask import Flask, jsonify, request, Response, abort, make_response
from bson.json_util import dumps
from time import gmtime, strftime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_pymongo import PyMongo
from flask_cors import CORS, cross_origin
from models.user import User
from datetime import datetime, timedelta
from bson import ObjectId
from time import time
import jwt
import pymongo
from pymongo import MongoClient
from PalrWebService import app

app = Flask(__name__)
import pymongo
from pymongo import MongoClient
from PalrWebService import app

app.config['MONGO_HOST'] = 'ds044989.mlab.com'
app.config['MONGO_PORT'] = 44989
app.config['MONGO_DBNAME'] = 'palrdb'
app.config['MONGO_USERNAME'] = 'admin'
app.config['MONGO_PASSWORD'] = 'admin'

MONGODB_URI = 'mongodb://admin:admin@ds044989.mlab.com:44989/palrdb'

CORS(app)

app.config['SECRET_KEY'] = 'super-secret-key'

mongo = PyMongo(app, config_prefix='MONGO')

# Utility Functions
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

def user_to_map(user):
    return {
        'id': str(user.get("_id")),
        'name': user.get("name"),
        'email': user.get("email"),
        'location': user.get("location"),
        "gender": user.get('gender'),
        "age": user.get('age'),
        "inMatchProcess": user.get('in_match_process'),
        "isMatched": user.get('is_matched')
    }


# Functions for dealing with token generation and authorization
def parse_token(req):
    token = req.headers.get('Authorization')
    return jwt.decode(token, app.secret_key, algorithms='HS256')

def create_match(user_id_1, user_id_2):
    # Create the conversation data
    conversation_data_id = mongo.db.conversation_data.insert({"isPermanent": False, "lastMessageSent": None})

    ts = time()
    isodate = datetime.fromtimestamp(ts, None)
    conversation_id = mongo.db.conversations.insert({"user": user_id_1, "pal": user_id_2, "conversation_data_id": conversation_data_id, "created_at": isodate, "last_message_date": isodate})

    # Set the above users matched to true
    mongo.db.users.update({"_id": ObjectId(user_id_1)}, {"$set": {"is_matched": True}})
    mongo.db.users.update({"_id": ObjectId(user_id_1)}, {"$set": {"in_match_process": False}})
    mongo.db.users.update({"_id": ObjectId(user_id_2)}, {"$set": {"is_matched": True}})
    mongo.db.users.update({"_id": ObjectId(user_id_2)}, {"$set": {"in_match_process": False}})

# Error Handling
@app.errorhandler(400)
def respond400(error):
    response = jsonify({'message': error.description['message']})
    response.status_code = 400
    return response

@app.route('/login', methods=['POST'])
@cross_origin()
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

    user_id = str(user_document['_id'])
    token = create_token(user_id)
    resp = jsonify({"accessToken": token,
                    "userId": user_id})

    return resp

@app.route('/register', methods = ['POST'])
@cross_origin()
def register():
    name = request.get_json().get('name')
    password = request.get_json().get('password')
    email = request.get_json().get('email')
    location = request.get_json().get('location')

    if name is None or password is None or email is None:
        # missing arguments
        abort(400, {'message': 'Missing required parameters' \
                ' name, password, email, and location are ALL required.'})

    # Should do error checking to see if user exists already
    if mongo.db.users.find({"email": email}).count() > 0:
        # Email already exists
        error_message = "A user with the email " + email + " already not exists."
        abort(400, {'message': error_message})


    _id = mongo.db.users.insert({"name": name, "password": generate_password_hash(password), "email" : email, "location": location, "in_match_process": False, "is_matched": False})

    user = User(str(_id), name, password, email, location)

    # Now we have the Id, we need to create a jwt access token
    # and send the corresponding response back
    token = create_token(user.id)
    resp = jsonify({"accessToken": token,
                    "userId": str(_id)})

    return resp

@app.route("/match", methods=['POST'])
def match():
    payload = parse_token(request)
    user_id = payload['sub']

    # Check if this user is already
    # in the pool to be matched
    user_document = mongo.db.users.find_one({'_id': ObjectId(user_id)})

    # Check if the user is already matched
    is_matched = user_document.get('is_matched')

    if is_matched is True:
        error_message = "This user has already been matched."
        abort(400, {'message': error_message})


    user_in_match_process = user_document.get('in_match_process')
    if user_in_match_process is True:
        return dumps({'success':True}), 200, {'ContentType':'application/json'}

    # Check our users collection to see if there
    # is someone to match with us
    cursor = mongo.db.users.find({})
    for record in cursor:
        in_match_process = record.get('in_match_process')
        if in_match_process is True:
            # Match with this person
            matched_user_id = record.get('_id')
            create_match(user_id, matched_user_id)
            break

    mongo.db.users.update({"_id": ObjectId(user_id)}, {"$set": {"in_match_process": True}})

    return dumps({'success':True}), 200, {'ContentType':'application/json'}

@app.route("/users/<user_id>", methods=['GET'])
def user(user_id):
    user_document = mongo.db.users.find_one({'_id': ObjectId(user_id)})

    if user_document is None:
        error_message = "The user with id " + user_id + " does not exist."
        abort(400, {'message': error_message})

    resp = jsonify({
                    "name": user_document.get('name'),
                    "email": user_document.get('email'),
                    "location": user_document.get('location'),
                    "gender": user_document.get('gender'),
                    "age": user_document.get('age'),
                    "inMatchProcess": user_document.get('in_match_process'),
                    "isMatched": user_document.get('is_matched')
                    })

    return resp

@app.route("/conversations", methods=['GET'])
def conversations():
    payload = parse_token(request)
    user_id = payload['sub']

    conversations_list = []

    # get all the conversations for current user
    conversations = mongo.db.conversations.find({'user': user_id})

    for record in conversations:
        # Get relevent information for encoding
        user_document = user_to_map(mongo.db.users.find_one({'_id': ObjectId(record.get('user'))}))
        pal_document = user_to_map(mongo.db.users.find_one({'_id': record.get('pal')}))
        conversation_id = str(record.get('_id'))
        conversation_data_id = str(record.get('conversation_data_id'))
        last_message_date = str(record.get('last_message_date'))
        data = {
            'id': conversation_id,
            'user': user_document,
            'pal': pal_document,
            'createdAt': record.get("created_at"),
            'conversationDataId': conversation_data_id,
            'lastMessageDate': last_message_date
        }
        conversations_list.append(data)

    return make_response(dumps(conversations_list))

@app.route("/messages", methods=['GET', 'POST'])
def messages():
    if request.method =='POST':
        send_message(request)
    else:
        get_messages(request)

def get_messages(request):
    print "Get message executing"
    payload = parse_token(request)
    conversation_data_id = request.args.get('conversationDataId')
    limit = request.args.get('limit')
    offset = request.args.get('offset')

    if conversation_data_id is None:
        # invalid query parameters
        error_message = "The parameter conversationDataId was missing."
        abort(400, {'message': error_message})

    # default limit is 20
    if limit is None:
        limit = 20

    #default offset is 0
    if offset is None:
        offset = 0
    messages = []

    #get messages associated with the conversationDataId
    cursor = mongo.db.messages.find({"conversation_data_id": conversation_data_id}).sort('created_at', pymongo.DESCENDING)

    if len(cursor) > offset or limit != 0:
        i = 0
        j = 0
        for record in cursor:
            if i < cursor:
                i+=1
                continue
            if j < limit:
                j+=1
                # Get relevant information for encoding
                data = {
                    'id': str(record.get('_id')),
                    'conversationDataId': conversation_data_id,
                    'createdBy': record.get('created_by'),
                    'createdAt': str(record.get('created_at')),
                    'content': record.get('content')
                }
                messages.append(data)

        print messages
        return make_response(dumps(messages))

def send_message(request):
    print "Send Message executing"
    payload = parse_token(request)

    # Get the request body
    req_body = request.get_json()

    content = req_body.get('content')
    conversation_data_id = req_body.get('conversationDataId')
    created_by = req_body.get('createdById')

    # validate
    if content is None or conversation_data_id is None or created_by is None:
        # invalid query parameters
        error_message = "Error in the request body. All of content, conversationDataId and createdById are needed."
        abort(400, {'message': error_message})

    # get the current time
    ts = time()
    isodate = datetime.fromtimestamp(ts, None)

    # update conversations last update data
    conversation_cursor = mongo.db.conversations.find({"conversation_data_id": conversation_data_id})
    for record in conversation_cursor:
        mongo.db.conversations.update({"_id": record.get('_id')}, {"$set": {"last_message_date": isodate}})

    # create the message
    message_id = mongo.db.messages.insert({"conversation_data_id": conversation_data_id, "created_at": isodate, "created_by": created_by, "content": content})

    # get the created message
    record = mongo.db.messages.find({"_id": message_id})
    message = {
        'id': str(record.get('_id')),
        'conversationDataId': conversation_data_id,
        'createdBy': record.get('created_by'),
        'createdAt': str(record.get('created_at')),
        'content': record.get('content')
    }
    return make_response(dumps(message))

if __name__ == "__main__":
    app.run()
