from flask import Blueprint

users_api = Blueprint('users', __name__)

@users_api.route("/users/<user_id>", methods=['GET'])
def user(user_id):
    user_document = mongo.db.users.find_one({'_id': ObjectId(user_id)})

    if user_document is None:
        error_message = "The user with id " + user_id + " does not exist."
        abort(400, {'message': error_message})

    resp = jsonify({
                    "id": str(user_document.get('_id')),
                    "name": user_document.get('name'),
                    "email": user_document.get('email'),
                    "location": user_document.get('location'),
                    "gender": user_document.get('gender'),
                    "age": user_document.get('age'),
                    "inMatchProcess": user_document.get('in_match_process'),
                    "isMatched": user_document.get('is_matched')
                    })

    return resp
