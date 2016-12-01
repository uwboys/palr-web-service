from flask import Blueprint

match_api = Blueprint('match', __name__)

'''
The following contains our endpoint defintions
'''

@match_api.route("/match", methods=['POST'])
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

@match_api.route("/match/permanent", methods=['POST'])
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


'''
The following are utility methods we use for servicing requests
for our the routes above.
'''

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
