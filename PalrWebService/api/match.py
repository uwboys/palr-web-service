from flask import Blueprint

match_api = Blueprint('match', __name__)

'''
The following contains our endpoint defintions
'''

@match_api.route("/match", methods=['POST'])
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
            create_match(ObjectId(user_id), matched_user_id)
            return dumps({'success':True}), 200, {'ContentType':'application/json'}

    mongo.db.users.update({"_id": ObjectId(user_id)}, {"$set": {"in_match_process": True}})

    return dumps({'success':True}), 200, {'ContentType':'application/json'}

'''
The following are utility methods we use for servicing requests
for our the routes above.
'''

def create_match(user_id_1, user_id_2):
    # Create the conversation data
    conversation_data_id = mongo.db.conversation_data.insert({"isPermanent": False, "lastMessageSent": None})

    ts = time()
    isodate = datetime.fromtimestamp(ts, None)
    mongo.db.conversations.insert({"user": user_id_1, "pal": user_id_2, "conversation_data_id": conversation_data_id, "created_at": isodate, "last_message_date": isodate})
    mongo.db.conversations.insert({"user": user_id_2, "pal": user_id_1, "conversation_data_id": conversation_data_id, "created_at": isodate, "last_message_date": isodate})

    # Set the above users matched to true
    mongo.db.users.update({"_id": ObjectId(user_id_1)}, {"$set": {"is_matched": True}})
    mongo.db.users.update({"_id": ObjectId(user_id_1)}, {"$set": {"in_match_process": False}})
    mongo.db.users.update({"_id": ObjectId(user_id_2)}, {"$set": {"is_matched": True}})
    mongo.db.users.update({"_id": ObjectId(user_id_2)}, {"$set": {"in_match_process": False}})

    return

