""" 
This file contains the blueprint and endpoint definitions
for user authentication, which includes users registering,
and LOGging into the application.
"""

from flask import Blueprint, jsonify, request, Response, abort, make_response
from api import parse_token

message_api = Blueprint('message', __name__)

'''
The following contains our endpoint defintions
'''

@app.route('/messages', methods=['GET', 'POST'])
def messages():
    if request.method == 'POST':
        return send_message(request)
    elif request.method == 'GET':
        return get_messages(request)
    else:
        # Unsupported method
        error_message = 'The method is not supported for this endpoint.'
        abort(400, error_message)

'''
The following are utility methods we use for servicing requests
for our the routes above.
'''

def send_message(request):
    LOG.info('Parsing authentication token... ')
    payload = parse_token(request)

    LOG.info('A user is attempting to send messages.')

    req_body = request.get_json()

    content = req_body.get('content')
    conversation_data_id = req_body.get('conversationDataId')

    # Error checking
    if not content or not conversation_data_id or content is None or conversation_data_id is None:
        LOG.error('The message content and/or the conversation_data_id is non-existent or malformed!')
        error_message = "Error in the request body. The message content and/or the conversationDataId are malformed!"
        abort(400, error_message)

    LOG.info('Updating conversation last updated data.')

    # update conversations last update data
    conversation_cursor = db.Conversation.find({'conversation_data_id': conversation_data_id})
    for record in conversation_cursor:
        db.Conversations.update({"_id": record.get('_id')}, {"$set": {"last_message_date": datetime.utcnow()}})

    LOG.info('Creating and inserting the new message into the DB... ')
    message_id = db['palrdb'].Message.insert({
        'conversation_data_id': ObjectId(conversation_data_id), 
        'created_at': datetime.utcnow(), 
        'created_by': ObjectId(created_by), 
        'content': content
    })

    user_document = user_to_map(db.User.find_one({'_id': ObjectId(created_by)}))
    created_by = payload['sub']

    # get the created message
    LOG.debug('Getting the newly created message... ')
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
