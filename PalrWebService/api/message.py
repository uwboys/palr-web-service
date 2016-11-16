from flask import Blueprint

message_api = Blueprint('message', __name__)

'''
The following contains our endpoint defintions
'''

@message_api.route("/messages", methods=['GET', 'POST'])
def messages():
    if request.method =='POST':
        return send_message(request)
    else:
        return get_messages(request)

'''
The following are utility methods we use for servicing requests
for our the routes above.
'''

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
    ts = time()
    isodate = datetime.fromtimestamp(ts, None)


    # update conversations last update data
    conversation_cursor = mongo.db.conversations.find({"conversation_data_id": conversation_data_id})
    for record in conversation_cursor:
        mongo.db.conversations.update({"_id": record.get('_id')}, {"$set": {"last_message_date": isodate}})

    # create the message

    print datetime.now()
    message_id = mongo.db.messages.insert({"conversation_data_id": ObjectId(conversation_data_id), "created_at": datetime.now(), "created_by": ObjectId(created_by), "content": content})
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

    return make_response(dumps(message))
