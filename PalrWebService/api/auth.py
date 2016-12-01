# -*- coding: utf-8 -*- 

""" 
This file contains the blueprint and endpoint definitions
for user authentication, which includes users registering,
and LOGging into the application.
"""

import jwt
import re

from datetime import datetime, timedelta

from config import Config
from extensions import LOG, db
from models.user import User

from werkzeug.security import generate_password_hash, check_password_hash

from flask import jsonify, request, Blueprint, abort

auth_api = Blueprint('auth', __name__)

'''
The following contains our endpoint defintions
'''

@auth_api.route('/register', methods = ['POST'])
def register():
    LOG.info('A user is attempting to register with the application.')

    # We use this regex to verify that passed in emails are in correct email format.
    regex = "^[a-zA-Z0-9.!#$%&’*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$" 

    req_body = request.get_json()

    name = req_body.get('name')
    password = req_body.get('password')
    email = req_body.get('email')
    country = req_body.get('country')

    LOG.debug('The user is trying to register with the following info:')
    LOG.debug('name: %s', name)
    LOG.debug('password: %s', password)
    LOG.debug('email: %s', email)
    LOG.debug('country: %s', country)

    # Error checking
    if not name or not password or not email or not country or name is None or password is None or email is None or not re.match(regex, email):
        error_message = 'The passed in information for registration is invalid or malformed.'
        LOG.error(error_message)
        abort(400, error_message)

    # Error checking to see if the specified email already exists
    if db.User.find({"email": email}).count() > 0:
        error_message = "A user with the email " + email + " already exists."
        LOG.error(error_message)
        abort(400, error_message)

    LOG.debug('A user with the email %s does not exist, therefore we will register this person as a new user.', email)

    image_url = "http://res.cloudinary.com/palr/image/upload/v1479864897/default-profile-pic_gmwop0.jpg"

    user_collection = db['palrdb'].users
    _id = user_collection.insert_one({   
        "name": name, 
        "password": generate_password_hash(password), 
        "email" : email, 
        "country": country, 
        "in_match_process": False, 
        "is_temporarily_matched": False,
        "is_permanently_matched": False,
        "matched_with": [],
        "image_url": image_url
    })

    # Now we have the Id, we need to create a jwt access token
    # and send the corresponding response back
    LOG.debug('The user with email %s has successfully registered and is now logged in.', email)

    token = __create_token(str(_id))
    resp = jsonify({"accessToken": token,
        "userId": str(_id)})

    return resp

@auth_api.route('/login', methods=['POST'])
def login():
    """ The login route. This is the api endpoing users hit to login to the application """ 
    LOG.info('A user is attempting to login to the application.')

    email = request.get_json().get('email')
    password = request.get_json().get('password')

    LOG.debug('The user trying to login has an email %s and a password %s', email, password)

    # Error checking
    if not email or not password or email is None or password is None:
        LOG.error('The passed in login credentials are malformed!')
        error_message = 'The passed in email and/or password is malformed! Request aborted.'
        abort(400, error_message)


    LOG.info('Retrieving the user with email %s from the database...', email)

    user_cursor = db.User.find({'email': email})
    if user_cursor.count() == 0:
        # The specified user does not exist
        LOG.error('A user with the email %s does not exist! Request aborted.', email)
        error_message = "A user with the email " + email + " does not exist."
        abort(400, error_message)


    user = user_cursor.next()

    if not check_password_hash(user['password'], password):
        # The password is invalid for this user
        LOG.error('The password for user with email %s is invalid!', password)
        error_message = "Invalid password for " + email + "."
        abort(400, error_message)

    # If we are here, then the user has successfully logged in,
    # and we assign authentication tokens.
    LOG.info('The user with email %s has successfully logged in.', email)

    user_id = str(user._id)
    token = __create_token(user_id)
    resp = jsonify({"accessToken": token,
        "userId": user_id})

    return resp

'''
The following are utility methods we use for servicing requests
for our the routes above.
'''

def parse_token(req):
    token = req.headers.get('Authorization')
    return jwt.decode(token, app.secret_key, algorithms='HS256')

def __create_token(user_id):
    payload = {
        # subject
        'sub': user_id,
        #issued at
        'iat': datetime.utcnow(),
        #expiry
        'exp': datetime.utcnow() + timedelta(days=3)
    }

    token = jwt.encode(payload, Config.SECRET_KEY, algorithm='HS256')
    return token.decode('unicode_escape')
