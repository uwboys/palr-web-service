""" 
This file contains the blueprint for error handlers
for our api endpoints.
"""

from flask import jsonify, abort, Blueprint

error_handlers = Blueprint('error_handlers', __name__)

@error_handlers.app_errorhandler(400)
def bad_request(error):
    return __errorMessage('bad_request', error.description, 400)

@error_handlers.app_errorhandler(401)
def unauthorized(error):
    return __errorMessage('unauthorized', error.description, 400)

@error_handlers.app_errorhandler(403)
def forbidden(error):
    return __errorMessage('forbidden', error.description, 400)

@error_handlers.app_errorhandler(404)
def not_found(error):
    return __errorMessage('not_found', error.description, 400)

'''
The following are utility methods we use for servicing the
errors above.
'''

def __errorMessage(error, message, status_code):
    errorMessage = jsonify({
        'error': error, 
        'message': message,
        'status_code': status_code
    })

    return errorMessage
