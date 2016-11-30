# -*- coding: utf-8 -*-
from flask import Flask, jsonify, request, Response, abort, make_response
from bson.json_util import dumps
from time import gmtime, strftime, time
from werkzeug.security import generate_password_hash, check_password_hash
from flask_pymongo import PyMongo
from flask_cors import CORS, cross_origin
from models.user import User
from global_constants import global_countries, global_ethnicities
from datetime import datetime, timedelta
from bson import ObjectId
import atexit
import jwt
import logging
import pymongo
import re
import validators
import global_constants
from pymongo import MongoClient
from flask_socketio import SocketIO, emit
from flask import Flask
from flask import session
from flask_socketio import emit, join_room, leave_room
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from random import randint

app = Flask(__name__)

app.config['MONGO_HOST'] = 'ds044989.mlab.com'
app.config['MONGO_PORT'] = 44989
app.config['MONGO_DBNAME'] = 'palrdb'
app.config['MONGO_USERNAME'] = 'admin'
app.config['MONGO_PASSWORD'] = 'admin'

MONGODB_URI = 'mongodb://admin:admin@ds044989.mlab.com:44989/palrdb'

CORS(app)

app.config['SECRET_KEY'] = 'super-secret-key'

socketio = SocketIO(app)

mongo = PyMongo(app, config_prefix='MONGO')

log = logging.getLogger('apscheduler.executors.default')
log.setLevel(logging.INFO)  # DEBUG

fmt = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
h = logging.StreamHandler()
h.setFormatter(fmt)
log.addHandler(h)

# Utility functions to clean conversations
def purge_old_conversations():
    with app.app_context():
        current_time = datetime.utcnow()
        conversations = mongo.db.conversations.find({'is_permanent': False})
        for conversation in conversations:
            created_at = str(conversation.get('created_at'))
            user = conversation.get('user')
            pal = conversation.get('pal')
            created_at_datetime = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S.%f+00:00")
            diff = current_time - created_at_datetime
            if diff.days > 3:
                mongo.db.conversations.remove({'_id': ObjectId(conversation.get('_id'))})
                update_user_field(user, "is_temporarily_matched", False)
                update_user_field(pal, "is_temporarily_matched", False)
                emit_to_clients(str(user), 'delete_conversation', dumps({"conversation_id": str(coversation.get('_id'))}))


scheduler = BackgroundScheduler()
scheduler.add_job(
    func=purge_old_conversations,
    trigger=IntervalTrigger(hours=1),
    id='purge_conversations_job',
    name='Deletes temporary conversations that are older than 3 days',
    replace_existing=True)
scheduler.start()
# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())


# Utility Functions for Users
def user_to_map(user):
    country = user.get("country")
    if country is not None:
        country = str(country).title()
    ethnicity = user.get('ethnicity')
    if ethnicity is not None:
        ethnicity = str(ethnicity).title()
    return {
            'id': str(user.get("_id")),
            'name': user.get("name"),
            'email': user.get("email"),
            'country': country,
            "gender": user.get('gender'),
            "age": user.get('age'),
            "ethnicity": ethnicity,
            "inMatchProcess": user.get('in_match_process'),
            "isTemporarilyMatched": user.get('is_temporarily_matched'),
            "isPermanentlyMatched": user.get('is_permanently_matched'),
            "imageUrl": user.get('image_url'),
            "hobbies": user.get('hobbies')
        }

def user_document_by_id(user_id):
    return mongo.db.users.find_one({'_id': ObjectId(user_id)})

def user_response_by_id(user_id):
    user_document = mongo.db.users.find_one({'_id': ObjectId(user_id)})

    if user_document is None:
        error_message = "The user with id " + user_id + " does not exist."
        abort(400, {'message': error_message})
    
    resp = user_to_map(user_document)
    return resp

def update_user_field (user_id, field, value):
    mongo.db.users.update({"_id": ObjectId(user_id)}, {"$set": { field: value}})

# Utility Functions for Matching
# Internal function to determine match type
def get_match_type (user_id):
    user_document = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    return user_document.get("match_type")

# Get match value for the talk type
def get_match_value_for_talk(user_id_1, user_id_2):
    user1 = user_response_by_id(user_id_1)
    user2 = user_response_by_id(user_id_2)
    points = 0
    if not user1.get('country') is None or not user2.get('country') is None or not user1.get('ethnicity') is None or not user2.get('ethnicity') is None:
        if user1.get('country') == user2.get('country') and user1.get('ethnicity') == user2.get('ethnicity'):
            return -1
    
    if get_match_type(user_id_2) == "talk":
        points += 5
    elif get_match_type(user_id_2) == "listen":
        points += 20
    else:
        points += 5

    if user1.get('country') != user2.get('country'):
        points += 5
    else:
        points -= 5

    if user1.get('ethnicity') != user2.get('ethnicity'):
        points += 5
    else:
        points -= 5

    if user1.get('gender') != user2.get('gender'):
        points += 5

    return points

# Get match value for the listen type
def get_match_value_for_listen(user_id_1, user_id_2):
    user1 = user_response_by_id(user_id_1)
    user2 = user_response_by_id(user_id_2)
    points = 0
    if not user1.get('country') is None or not user2.get('country') is None or not user1.get('ethnicity') is None or not user2.get('ethnicity') is None:
        if user1.get('country') == user2.get('country') and user1.get('ethnicity') == user2.get('ethnicity'):
            return -1
    
    if get_match_type(user_id_2) == "talk":
        points += 20
    elif get_match_type(user_id_2) == "listen":
        points += 2
    else:
        points += 5

    if user1.get('country') != user2.get('country'):
        points += 5
    else:
        points -= 5

    if user1.get('ethnicity') != user2.get('ethnicity'):
        points += 5
    else:
        points -= 5

    if user1.get('gender') != user2.get('gender'):
        points += 5

    return points

# Get match value for the learn type
def get_match_value_for_learn(user_id_1, user_id_2):
    user1 = user_response_by_id(user_id_1)
    user2 = user_response_by_id(user_id_2)
    points = 0
    if not user1.get('country') is None or not user2.get('country') is None or not user1.get('ethnicity') is None or not user2.get('ethnicity') is None:
        if user1.get('country') == user2.get('country') and user1.get('ethnicity') == user2.get('ethnicity'):
            return -1
    
    if get_match_type(user_id_2) == "talk":
        points += 20
    elif get_match_type(user_id_2) == "listen":
        points += 20
    else:
        points += 50

    if user1.get('country') != user2.get('country'):
        points += 5
    else:
        points -= 5

    if user1.get('ethnicity') != user2.get('ethnicity'):
        points += 5
    else:
        points -= 5

    if user1.get('gender') != user2.get('gender'):
        points += 5

    return points

def not_already_permanently_matched(user, pal):
    conversations = mongo.db.conversations.find({'user': ObjectId(user)})
    
    for conversation in conversations:
        # If a conversation already exists between user and pal then it has to be a permanently matched conversation.
        if conversation.get('pal') == pal:
            return False

    return True

# Functions for dealing with token generation and authorization
def create_token(user_id):
    payload = {
            # subject
            'sub': user_id,
            #issued at
            'iat': datetime.utcnow(),
            #expiry
            'exp': datetime.utcnow() + timedelta(days=5)
            }

    token = jwt.encode(payload, app.secret_key, algorithm='HS256')
    return token.decode('unicode_escape')

def parse_token(req):
    token = req.headers.get('Authorization')
    return jwt.decode(token, app.secret_key, algorithms='HS256')

# Error Handling
@app.errorhandler(400)
def respond400(error):
    response = jsonify({'message': error.description['message']})
    response.status_code = 400
    return response

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

    user_id = str(user_document['_id'])
    token = create_token(user_id)
    resp = jsonify({"accessToken": token,
        "userId": user_id})

    return resp

@app.route('/register', methods = ['POST'])
def register():
    # Get the request body
    req_body = request.get_json()

    regex = "^[a-zA-Z0-9.!#$%&’*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$"

    name = req_body.get('name')
    password = req_body.get('password')
    email = req_body.get('email')
    country = req_body.get('country')

    if name is None or password is None or email is None:
        # missing arguments
        abort(400, {'message': 'Missing required parameters' \
                ' name, password, email, and country are ALL required.'})

    if type(email) == unicode:
        if not re.match(regex, email):
            error_message = "Provided email was invalid."
            abort(400, {'message': error_message})

        # Should do error checking to see if user exists already
    if mongo.db.users.find({"email": email}).count() > 0:
        # Email already exists
        error_message = "A user with the email " + email + " already exists."
        abort(400, {'message': error_message})


    _id = mongo.db.users.insert({   
                            "name": name, 
                            "password": generate_password_hash(password), 
                            "email" : email, 
                            "country": country, 
                            "in_match_process": False, 
                            "is_temporarily_matched": False,
                            "is_permanently_matched": False,
                            "matched_with": [],
                            "image_url": "http://res.cloudinary.com/palr/image/upload/v1479864897/default-profile-pic_gmwop0.jpg"
                        })

    user = User(str(_id), name, password, email, country)

    # Now we have the Id, we need to create a jwt access token
    # and send the corresponding response back
    token = create_token(user.id)
    resp = jsonify({"accessToken": token,
        "userId": str(_id)})

    return resp

@app.route("/match/permanent", methods=['POST'])
def match_permanently():
    payload = parse_token(request)
    user_id = payload['sub']

    # Get the request body
    req_body = request.get_json()

    conversation_id = req_body.get('conversationId')
    if conversation_id is None:
        error_message = "Missing required field or passing null value conversationId."
        abort(400, {'message': error_message})

    conversation_document = mongo.db.conversations.find_one({'_id': ObjectId(conversation_id)})


    mongo.db.conversations.update({"_id": ObjectId(conversation_id)}, {"$set": { "request_permanent": True}})

    conversations = mongo.db.conversations.find({'pal': ObjectId(user_id)})
    other_conversation = None
    
    for possible_other_conversation in conversations:
        if possible_other_conversation.get('user') == conversation_document.get('pal'):
            other_conversation = possible_other_conversation
            break

    if other_conversation is None:
        error_message = "Internal error. No matching conversation for with the given id."
        abort(400, {'message': error_message})        

    if other_conversation.get('request_permanent') is True:
        # Users can match again with someone else
        update_user_field(user_id, "is_temporarily_matched", False)
        update_user_field(str(other_conversation.get('user')), "is_temporarily_matched", False)
        update_user_field(user_id, "is_permanently_matched", True)
        update_user_field(str(other_conversation.get('user')), "is_permanently_matched", True)

        # Make conversation Permanent
        mongo.db.conversations.update({"_id": ObjectId(conversation_id)}, {"$set": { "is_permanent": True}})
        mongo.db.conversations.update({"_id": ObjectId(other_conversation.get('_id'))}, {"$set": { "is_permanent": True}})

        print "Emitting permanent match"
        emit_to_clients(str(user_id), 'permanent_match', dumps({"conversation_id": conversation_id}))
        emit_to_clients(str(other_conversation.get('user')), 'permanent_match', dumps({"conversation_id": str(other_conversation.get('user'))}))

        return dumps({"message": "Permanent Match Created."}), 200, {'Content-Type':'application/json'}

    return dumps({"message": "Waiting for other user to request to make the conversation permanent."}), 200, {'Content-Type':'application/json'}

def create_temporary_match(user_id_1, user_id_2):
    # Create the conversation data
    conversation_data_id = mongo.db.conversation_data.insert({"isPermanent": False, "lastMessageSent": None})

    print "printing ids..."
    print type(user_id_1)
    print type(user_id_2)

    isodate = datetime.utcnow()
    mongo.db.conversations.insert({"user": user_id_1, "pal": user_id_2, "conversation_data_id": conversation_data_id, "created_at": isodate, "last_message_date": isodate, "is_permanent": False, "request_permanent": False})
    mongo.db.conversations.insert({"user": user_id_2, "pal": user_id_1, "conversation_data_id": conversation_data_id, "created_at": isodate, "last_message_date": isodate, "is_permanent": False, "request_permanent": False})

    matchList1 = user_document_by_id(user_id_1).get("matched_with")
    matchList2 = user_document_by_id(user_id_2).get("matched_with")

    if matchList1 is None:
        matchList1 = []

    if matchList2 is None:
        matchList2 = []

    matchList1.append(user_id_2)
    matchList2.append(user_id_1)

    # Set the above users matched to true
    update_user_field(user_id_1, "is_temporarily_matched", True)
    update_user_field(user_id_1, "in_match_process", False)
    update_user_field(user_id_1, "matched_with", matchList1)
    update_user_field(user_id_2, "is_temporarily_matched", True)
    update_user_field(user_id_2, "in_match_process", False)
    update_user_field(user_id_2, "matched_with", matchList2)

    # Find common hobbies, insert message into messages for both user
    user_1_hobbies = mongo.db.users.find_one({'_id': ObjectId(user_id_1)}).get('hobbies')
    user_2_hobbies = mongo.db.users.find_one({'_id': ObjectId(user_id_2)}).get('hobbies')

    print "Hobbies..."
    print user_1_hobbies
    print user_2_hobbies
    if (user_1_hobbies is not None and user_2_hobbies is not None and len(user_1_hobbies) > 0 and len(user_2_hobbies) > 0):
        # We actually find the common hobbies, 
        common_hobbies = set(user_1_hobbies).intersection(user_2_hobbies)
        print "common hobbies"
        print common_hobbies

        random = randint(0,1)

        final_conversation = None

        created_by = None

        if common_hobbies is not None and len(common_hobbies) > 0:
            if random == 0:
                conversations = mongo.db.conversations.find({'user': user_id_2})

                for possible_other_conversation in conversations:
                    if possible_other_conversation.get('pal') == user_id_1:
                        final_conversation = possible_other_conversation
                        created_by = user_id_2
                        break
            elif random == 1:
                conversations = mongo.db.conversations.find({'user': user_id_1})

                for possible_other_conversation in conversations:
                    if possible_other_conversation.get('pal') == user_id_2:
                        final_conversation = possible_other_conversation
                        created_by = user_id_1
                        break

            # update conversations last update data
            print "Entering message into db"
            conversation_cursor = mongo.db.conversations.find({"conversation_data_id": final_conversation.get('conversation_data_id')})
            for record in conversation_cursor:
                mongo.db.conversations.update({"_id": record.get('_id')}, {"$set": {"last_message_date": isodate}})

            # create the message
            message = ""
            for common in common_hobbies:
                message += common + ", "

            message = message[:-2]

            message_id = mongo.db.messages.insert({"conversation_data_id": ObjectId(conversation_data_id), "created_at": datetime.utcnow(), "created_by": ObjectId(created_by), 
                                                    "content": "Hi there! Let's talk about " + str(message) + "!"})

    print "Emitting temporary match"
    emit_to_clients(str(user_id_1), 'temporary_match', dumps({"inMatchProcess": False, "isTemporarilyMatched": True}))
    emit_to_clients(str(user_id_2), 'temporary_match', dumps({"inMatchProcess": False, "isTemporarilyMatched": True}))

    return

@app.route("/match", methods=['POST'])
def match_temporarily():
    payload = parse_token(request)
    user_id = payload['sub']
    match_vector = {}

    # Get the request body
    req_body = request.get_json()

    # Get the match type
    match_type = req_body.get('type')

    if match_type is None:
        match_type = "talk"
    else:
        match_type = match_type.lower()

    # Update in database
    update_user_field(user_id, "match_type", match_type)

    # Check if this user is already
    # in the pool to be matched
    user_document = mongo.db.users.find_one({'_id': ObjectId(user_id)})

    # Check if the user is already matched
    is_temporarily_matched = user_document.get('is_temporarily_matched')

    if is_temporarily_matched is True:
        error_message = "This user is already in a temporary match."
        abort(400, {'message': error_message})


    user_in_match_process = user_document.get('in_match_process')
    user_temporarily_matched = user_document.get('is_temporarily_matched')
    matchedList = user_document.get('mached_with')
    if matchedList is None:
        matchedList = []
    if user_in_match_process is True:
        return dumps({"inMatchProcess": user_in_match_process, "isTemporarilyMatched": user_temporarily_matched}), 200, {'ContentType':'application/json'}

    # Check our users collection to see if there
    # is someone to match with us
    cursor = mongo.db.users.find({'in_match_process' : True})
    for record in cursor:
        if not_already_permanently_matched (user_id, str(record.get('_id'))):
            if not str(record.get('_id')) in matchedList:
                # Add to the match vector based on match type
                if match_type == "talk":
                    match_vector[str(record.get('_id'))] = get_match_value_for_talk(user_id, record.get('_id'))
                elif match_type == "listen":
                    match_vector[str(record.get('_id'))] = get_match_value_for_listen(user_id, record.get('_id'))
                else:  # learn
                    match_vector[str(record.get('_id'))] = get_match_value_for_learn(user_id, record.get('_id'))
        

    match_vector_keys = match_vector.keys()
    matched_user_id = None
    max_match_value = -1

    # Match with the most "different" person
    for key in match_vector_keys:
        if match_vector.get(key) > max_match_value:
            max_match_value = match_vector.get(key)
            matched_user_id = key

    # Found a match
    if not matched_user_id is None:
        create_temporary_match(ObjectId(user_id), ObjectId(matched_user_id))
        user_document = mongo.db.users.find_one({'_id': ObjectId(user_id)})
        user_in_match_process = user_document.get('in_match_process')
        user_temporarily_matched = user_document.get('is_temporarily_matched')
        return dumps({"inMatchProcess": user_in_match_process, "isTemporarilyMatched": user_temporarily_matched}), 200, {'ContentType':'application/json'}
            
    update_user_field(user_id, "in_match_process", True)
    user_document = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    user_in_match_process = user_document.get('in_match_process')
    user_temporarily_matched = user_document.get('is_temporarily_matched')
    
    return dumps({"inMatchProcess": user_in_match_process, "isTemporarilyMatched": user_temporarily_matched}), 200, {'ContentType':'application/json'}

@app.route("/users/<user_id>", methods=['GET'])
def user(user_id):
    return jsonify(user_response_by_id(user_id))

@app.route("/users/me", methods=['GET', 'PUT'])
@cross_origin()
def user_details():
    if request.method == 'GET':
        return get_user_details(request)
    else:
        print "registering user details"
        return register_user_details(request)

def get_user_details(request):
    payload = parse_token(request)
    user_id = payload['sub']
    return jsonify(user_response_by_id(user_id))

def register_user_details(request):
    payload = parse_token(request)
    user_id = payload['sub']

    regex = "^[a-zA-Z0-9.!#$%&’*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$"

    # Get the request body
    req_body = request.get_json()

    # Get the data from the request
    name = req_body.get('name')
    email = req_body.get('email')
    gender = req_body.get('gender')
    country = req_body.get('country')
    age = req_body.get('age')
    ethnicity = req_body.get('ethnicity')
    image_url = req_body.get('imageUrl')
    hobbies = req_body.get('hobbies')

    # Validate data
    if name is not None:
        if type(name) == unicode:
            if len(name) == 0:
                name = None
        else:
            error_message = "Name should be a string."
            abort(400, {'message': error_message})

    if email is not None:
        if type(email) == unicode:
            if len(email) == 0:
                error_message = "Provided email was empty."
                abort(400, {'message': error_message})
            if not re.match(regex, email):
                error_message = "Provided email was invalid."
                abort(400, {'message': error_message})
        else:
            error_message = "Email should be a string."
            abort(400, {'message': error_message})

    if gender is not None:
        if type(gender) == unicode:
            gender = gender.lower()
            if gender != "male" and gender != "female":
                error_message = "Gender can only be male or female"
                abort(400, {'message': error_message})
        else:
            error_message = "Gender should be a string."
            abort(400, {'message': error_message})

    if country is not None:
        if type(country) == unicode:
            if not country.title() in global_countries:
                error_message = "country is not a valid country."
                abort(400, {'message': error_message})    
            country = country.lower()
        else:
            error_message = "Country should be a string."
            abort(400, {'message': error_message})

    if age is not None:
        if type(age) is not int or age <= 0:
            error_message = "Age can only be a positive nonzero integer"
            abort(400, {'message': error_message})
    
    if ethnicity is not None:
        if type(ethnicity) == unicode:
            if not ethnicity.title() in global_ethnicities:
                error_message = "The ethnicity is not valid."
                abort(400, {'message': error_message})    
            ethnicity = ethnicity.lower()
        else:
            error_message = "Ethnicity should be a string."
            abort(400, {'message': error_message})

    if image_url is not None:
        if type(image_url) == unicode:
            if validators.url(image_url) is False:
                error_message = "Image Url is not a valid url"
                abort(400, {'message': error_message})
        else:
            error_message = "Image Url should be a string."
            abort(400, {'message': error_message})

    if hobbies is not None:
        if type (hobbies) != list:
            error_message = "Hobbies must be an array/list of strings."
            abort(400, {'message': error_message})        

    # Update non null fields
    if name is not None:
        update_user_field(user_id, "name", name)

    if email is not None:
        update_user_field(user_id, "email", email)

    if gender is not None:
        update_user_field(user_id, "gender", gender)

    if country is not None:
        update_user_field(user_id, "country", country)

    if age is not None:
        update_user_field(user_id, "age", age)

    if ethnicity is not None:
        update_user_field(user_id, "ethnicity", ethnicity)

    if image_url is not None:
        update_user_field(user_id, "image_url", image_url)        

    if hobbies is not None:
        update_user_field(user_id, "hobbies", hobbies)
    
    return jsonify(user_response_by_id(user_id))


@app.route("/conversations", methods=['GET'])
def conversations():
    payload = parse_token(request)
    user_id = payload['sub']

    conversations_list = []

    # get all the conversations for current user
    conversations = mongo.db.conversations.find({'user': ObjectId(user_id)})

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
                'createdAt': str(record.get("created_at")),
                'conversationDataId': conversation_data_id,
                'lastMessageDate': last_message_date,
                'isPermanent' : record.get("is_permanent"),
                'requestPermanent' : record.get("request_permanent")
                }
        conversations_list.append(data)

    return make_response(dumps(conversations_list))

def get_messages(request):
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
    cursor = mongo.db.messages.find({"conversation_data_id": ObjectId(conversation_data_id)}).sort('created_at', pymongo.DESCENDING)

    if cursor.count() > offset or limit != 0:
        i = 0
        j = 0
        for record in cursor:
            if i < offset:
                i+=1
                continue
            if j < limit:
                j+=1
                # Get relevant information for encoding
                user_document = user_to_map(mongo.db.users.find_one({'_id': record.get('created_by')}))

                data = {
                        'id': str(record.get('_id')),
                        'conversationDataId': conversation_data_id,
                        'createdBy': user_document,
                        'createdAt': str(record.get('created_at')),
                        'content': record.get('content')
                        }
                messages.append(data)
            else:
                break
        return make_response(dumps(messages))

clients = {}

def send_message(request):
    payload = parse_token(request)

    # Get the request body
    req_body = request.get_json()

    content = req_body.get('content')
    conversation_data_id = req_body.get('conversationDataId')
    created_by = payload['sub']

    # validate
    if content is None or conversation_data_id is None:
        # invalid query parameters
        error_message = "Error in the request body. Content and conversationDataId are needed."
        abort(400, {'message': error_message})

    # get the current time
    isodate = datetime.utcnow()


    # update conversations last update data
    conversation_cursor = mongo.db.conversations.find({"conversation_data_id": conversation_data_id})
    for record in conversation_cursor:
        mongo.db.conversations.update({"_id": record.get('_id')}, {"$set": {"last_message_date": isodate}})

    # create the message
    message_id = mongo.db.messages.insert({"conversation_data_id": ObjectId(conversation_data_id), "created_at": datetime.utcnow(), "created_by": ObjectId(created_by), "content": content})
    user_document = user_to_map(mongo.db.users.find_one({'_id': ObjectId(created_by)}))

    # get the created message
    record = mongo.db.messages.find_one({"_id": message_id})
    message = {
        'id': str(record.get('_id')),
        'conversationDataId': str(conversation_data_id),
        'createdBy': user_document,
        'createdAt': str(record.get('created_at')),
        'content': record.get('content')
    }

    conversation = mongo.db.conversations.find_one({"conversation_data_id": ObjectId(conversation_data_id),
                                                    "user": ObjectId(created_by)})

    pal_record_id = str(conversation.get('pal'))

    # Emit to that 
    emit_to_clients(pal_record_id, 'message', message)

    return make_response(dumps(message))

def emit_to_clients(user_id, event, data):
    # Emit to that 
    if user_id in clients:
        for socket in clients[user_id]:
            socket.emit(event, data)


# Object that represents a socket connection
class Socket:
    def __init__(self, sid):
        self.sid = sid
        self.connected = True

# Emits data to a socket's unique room
    def emit(self, event, data):
        emit(event, data, room=self.sid, namespace='/ws', incdude_self=False)


@app.route("/messages", methods=['GET', 'POST'])
def messages():
    if request.method =='POST':
        return send_message(request)
    else:
        return get_messages(request)

@socketio.on('add_client', namespace='/ws')
def add_client(access_token):
    payload = jwt.decode(access_token, app.secret_key, algorithms='HS256')
    user_id = payload['sub']

    print 'clients[' + user_id + '] = ' + request.sid

    if user_id in clients:
        clients[user_id].append(Socket(request.sid))
    else:
        sockets = [Socket(request.sid)]
        clients[user_id] = sockets

    join_room(request.sid)
    ''' 
    if user_id in clients:
        clients[user_id].append(request.sid)
    else:
        request_sid_array = [request.sid]
        clients[user_id] = request_sid_array
    '''

@socketio.on('connect', namespace='/ws')
def connected():
    print 'Establishing session connection'
    print request.sid

@socketio.on('disconnect', namespace='/ws')
def disconnected():
    print 'Disconnecting'
    print request
    # Remove this from clients
    leave_room(request.sid)
    for k, v in clients.items():
        if v[-1].sid == request.sid:
            print 'Deleting client with id ' + k
            v.pop()
            if len(v) == 0:
                print 'Deleting key'
                del clients[k]

    '''
    for k, v in clients.items():
        for sid in v:
            sid = [item for item in sid if sid != request.sid]
            if len(v) == 0:
                del clients[k]
                return
    '''


if __name__ == "__main__":
    socketio.run(app)
