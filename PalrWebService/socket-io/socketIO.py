from config import Config
from flask import Blueprint

socket_blueprint = Blueprint('socket', __name__)

clients = {}

@socketio.on('add_client', namespace='/ws')
def add_client(access_token):
    payload = jwt.decode(access_token, app.secret_key, algorithms='HS256')
    user_id = payload['sub']

    print 'clients[' + user_id + '] = ' + request.sid

    if user_id in clients:
        clients[user_id].append(Socket(request.sid))
    else:
        sockets = [Socket(request.sid)]
        clients[user_id] = sockets

    join_room(request.sid)

@socketio.on('connect', namespace='/ws')
def connected():
    print 'Establishing session connection'
    print request.sid

@socketio.on('disconnect', namespace='/ws')
def disconnected():
    print 'Disconnecting'
    print request
    # Remove this from clients
    leave_room(request.sid)
    for k, v in clients.items():
        if v[-1].sid == request.sid:
            print 'Deleting client with id ' + k
            v.pop()
            if len(v) == 0:
                print 'Deleting key'
                del clients[k]

def emit_to_clients(user_id, event, data):
    # Emit to that 
    if user_id in clients:
        for socket in clients[user_id]:
            socket.emit(event, data)

class Socket:
    ''' Object that represents a socket connection ''' 
    def __init__(self, sid):
        self.sid = sid
        self.connected = True

    def emit(self, event, data):
        ''' Emits data to a socket's unique room '''
        emit(event, data, room = self.sid, namespace = Config.SocketIOConfig.SOCKET_IO_NAMESPACE)
