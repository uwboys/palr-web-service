from flask import Blueprint
from flask_cors import cross_origin
from models.user import User
from errors import bad_request

auth_api = Blueprint('auth', __name__)

'''
The following contains our endpoint defintions
'''

@auth_api.route('/login', methods=['POST'])
@cross_origin()
def login():
    email = request.get_json().get('email')
    password = request.get_json().get('password')

    cursor = mongoConnection.User.find({"email": email})

    if cursor.count() == 0:
        error_message = "A user with the email " + email + " does not exist."
        bad_request(error_message)

    user_document = cursor.next()

    '''
    if not check_password_hash(user_document['password'], password):
        error_message = "Invalid password for " + email + "."
        abort(400, {'message': error_message})

    user_id = str(user_document['_id'])
    token = create_token(user_id)
    resp = jsonify({"accessToken": token,
                    "userId": user_id})

    '''

    return 'hello'

@auth_api.route('/register', methods = ['POST'])
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

'''
The following are utility methods we use for servicing requests
for our the routes above.
'''

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

# Functions for dealing with token generation and authorization
def parse_token(req):
    token = req.headers.get('Authorization')
    return jwt.decode(token, app.secret_key, algorithms='HS256')
