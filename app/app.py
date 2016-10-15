from flask import Flask, jsonify, request
app = Flask(__name__)


@app.route('/palr/api/v1.0/login', methods=['POST'])
def login():
    json = request.get_json()
    print json
    return "hello"

@app.route('/', methods=['GET'])
def init():
    return "Hello, world"


@app.route('/palr/api/v1.0/register', methods = ['POST'])
def new_user():
    username = request.get_json().get('username')
    password = request.get_json().get('password')

    if username is None or password is None:
        abort(400) # missing arguments
    if User.query.filter_by(username = username).first() is not None:
        abort(400) # existing user

    user = User(username = username)
    user.hash_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({ 'username': user.username }), 201, {'Location': url_for('get_user', id = user.id, _external = True)}

if __name__ == "__main__":
    app.run()
