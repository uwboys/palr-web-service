from flask import Blueprint

conversations_api = Blueprint('conversations', __name__)

'''
The following contains our endpoint defintions
'''

@conversations_api.route("/conversations", methods=['GET'])
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
            'lastMessageDate': last_message_date
        }
        conversations_list.append(data)

    return make_response(dumps(conversations_list))
