from flask import Blueprint
'''
The following contains our utility functions
'''
utility_blueprint = Blueprint('utility', __name__)

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

