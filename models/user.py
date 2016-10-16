from werkzeug.security import generate_password_hash, check_password_hash

class User(): 
    def __init__(self, _id, name, password, email, location = None):
        self._id = _id
        self._name = name
        self._password = password
        self._email = email
        self._location = location

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def email(self):
        return self._email

    @property
    def location(self):
        return self._location
