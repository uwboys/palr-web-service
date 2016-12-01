from flask import Blueprint

users_api = Blueprint('users', __name__)

@users_api.route("/users/<user_id>", methods=['GET'])
def user(user_id):
    return jsonify(user_response_by_id(user_id))

@users_api.route("/users/me", methods=['GET', 'PUT'])
def user_details():
    if request.method == 'GET':
        return get_user_details(request)
    else:
        print "registering user details"
        return register_user_details(request)

def get_user_details(request):
    payload = parse_token(request)
    user_id = payload['sub']
    return jsonify(user_response_by_id(user_id))

def register_user_details(request):
    payload = parse_token(request)
    user_id = payload['sub']

    regex = "^[a-zA-Z0-9.!#$%&’*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$"

    # Get the request body
    req_body = request.get_json()

    # Get the data from the request
    name = req_body.get('name')
    email = req_body.get('email')
    gender = req_body.get('gender')
    country = req_body.get('country')
    age = req_body.get('age')
    ethnicity = req_body.get('ethnicity')
    image_url = req_body.get('imageUrl')
    hobbies = req_body.get('hobbies')

    # Validate data
    if name is not None:
        if type(name) == unicode:
            if len(name) == 0:
                name = None
        else:
            error_message = "Name should be a string."
            abort(400, {'message': error_message})

    if email is not None:
        if type(email) == unicode:
            if len(email) == 0:
                error_message = "Provided email was empty."
                abort(400, {'message': error_message})
            if not re.match(regex, email):
                error_message = "Provided email was invalid."
                abort(400, {'message': error_message})
        else:
            error_message = "Email should be a string."
            abort(400, {'message': error_message})

    if gender is not None:
        if type(gender) == unicode:
            gender = gender.lower()
            if gender != "male" and gender != "female":
                error_message = "Gender can only be male or female"
                abort(400, {'message': error_message})
        else:
            error_message = "Gender should be a string."
            abort(400, {'message': error_message})

    if country is not None:
        if type(country) == unicode:
            if not country.title() in global_countries:
                error_message = "country is not a valid country."
                abort(400, {'message': error_message})    
            country = country.lower()
        else:
            error_message = "Country should be a string."
            abort(400, {'message': error_message})

    if age is not None:
        if type(age) is not int or age <= 0:
            error_message = "Age can only be a positive nonzero integer"
            abort(400, {'message': error_message})
    
    if ethnicity is not None:
        if type(ethnicity) == unicode:
            if not ethnicity.title() in global_ethnicities:
                error_message = "The ethnicity is not valid."
                abort(400, {'message': error_message})    
            ethnicity = ethnicity.lower()
        else:
            error_message = "Ethnicity should be a string."
            abort(400, {'message': error_message})

    if image_url is not None:
        if type(image_url) == unicode:
            if validators.url(image_url) is False:
                error_message = "Image Url is not a valid url"
                abort(400, {'message': error_message})
        else:
            error_message = "Image Url should be a string."
            abort(400, {'message': error_message})

    if hobbies is not None:
        if type (hobbies) != list:
            error_message = "Hobbies must be an array/list of strings."
            abort(400, {'message': error_message})        

    # Update non null fields
    if name is not None:
        update_user_field(user_id, "name", name)

    if email is not None:
        update_user_field(user_id, "email", email)

    if gender is not None:
        update_user_field(user_id, "gender", gender)

    if country is not None:
        update_user_field(user_id, "country", country)

    if age is not None:
        update_user_field(user_id, "age", age)

    if ethnicity is not None:
        update_user_field(user_id, "ethnicity", ethnicity)

    if image_url is not None:
        update_user_field(user_id, "image_url", image_url)        

    if hobbies is not None:
        update_user_field(user_id, "hobbies", hobbies)
    
    return jsonify(user_response_by_id(user_id))
