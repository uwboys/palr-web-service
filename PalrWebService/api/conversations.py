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
                'lastMessageDate': last_message_date,
                'isPermanent' : record.get("is_permanent"),
                'requestPermanent' : record.get("request_permanent")
                }
        conversations_list.append(data)

    return make_response(dumps(conversations_list))


'''
The following are utility methods we use for servicing requests
for our the routes above.
'''

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
