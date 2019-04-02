from flask import Blueprint, request
import api.AuthorizationAPI
from services.DBConn import db
import json
from bson import json_util
import time

messaging_api = Blueprint('messaging_api', __name__)
convoDB = db.conversations

current_milli_time = lambda: int(round(time.time() * 1000))


@messaging_api.route("/myConvos", methods=['GET'])
@api.AuthorizationAPI.requires_auth
def getConvoList():
    username = request.userNameFromToken

    try:
        records = convoDB.find({'participants': username}, {'_id': 0, 'participants': 1})
        return json.dumps(list(records))
    except Exception as e:
        print(e)
        return json.dumps({'error': "Server error while pulling convos.", 'code': 9})


@messaging_api.route("/getMessages", methods=['POST'])
@api.AuthorizationAPI.requires_auth
def getMessages():
    username = request.userNameFromToken
    data = request.get_json()
    page = data['page']
    participants = data['participants']

    records = convoDB.find({'participants': participants}, { '_id': 0, 'messages': {'$slice': [(20 * page), 20]}})
    return json.dumps(list(records))


@messaging_api.route("/sendMessage", methods=['POST'])
@api.AuthorizationAPI.requires_auth
def sendMessage():
    username = request.userNameFromToken
    data = request.get_json()
    if not ('message' in data):
        return json.dumps({'error': "'message' not provided.", 'code': -1})
    if not ('recipients' in data):
        return json.dumps({'error': "'recipients' not provided.", 'code': -2})

    message = data['message']
    to = data['recipients']

    participants = to
    participants.append(username)
    print(participants)
    try:
        record = convoDB.find_one({'participants': participants}, {'_id': 1})
        if record is None:  # Create conversation with all the participants
            newConvo = {
                'participants': participants,
                'messages': []
            }
            result = convoDB.insert_one(newConvo)  # Upload that list to the server.
            if result.inserted_id:
                print("New convo created.")
            else:
                return json.dumps({'error': "Failed to create new convo.", 'code': 1})
    except Exception as e:
        print(e)
        return json.dumps({'error': "Server error while trying to create new convo.", 'code': -9})

    # Add message to convo
    try:
        message = {'sender': username, 'message': message, 'time': current_milli_time()}
        convoDB.update({'participants': participants}, {'$push': {'messages': {'$each': [message], '$sort': {'time': -1}}}})
        return json.dumps({'success': True})
    except Exception as e:
        print(e)
        return json.dumps({'error': "Server error while adding message to convo.", 'code': 9})

