from flask import Blueprint, request
import api.AuthorizationAPI
from services.DBConn import db
import json
from bson import json_util
from bson.objectid import ObjectId
import time

messaging_api = Blueprint('messaging_api', __name__)
convoDB = db.conversations

current_milli_time = lambda: int(round(time.time() * 1000))


@messaging_api.route("/myConvos", methods=['GET'])
@api.AuthorizationAPI.requires_auth
def getConvoList():
    username = request.userNameFromToken

    try:
        records = convoDB.find({'participants': username}, {'_id': 1, 'participants': 1})
        listed = list(records)
        return json.dumps(listed, default=json_util.default)
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

    records = convoDB.find({'participants': participants}, {'messages': {'$slice': [(20 * page), 20]}})
    return json.dumps(records)


@messaging_api.route("/sendMessage", methods=['POST'])
@api.AuthorizationAPI.requires_auth
def sendMessage():
    username = request.userNameFromToken
    data = request.get_json()
    message = data['message']
    to = data['recipients']

    participants = to.append(username)

    record = convoDB.find({'participants': participants}, {'_id': 1})

    if record is None: # Create conversation with all the participants
        participants = to.append(username)
        newConvo = {
            'participants': participants,
            'messages': []
        }
        result = convoDB.insert_one(newConvo)  # Upload that list to the server.

        if result.inserted_id:
            print("New convo created.")
        else:
            return json.dumps({'error': "Failed to create new convo.", 'code': 1})

    # Add message to convo
    try:
        message = {'sender': username, 'message': message, 'time': current_milli_time()}
        convoDB.update({'participants': participants}, {'$push': {'messages': {'$each': [message], '$sort': {'time': -1}}}})
        return json.dumps({'success': True})
    except Exception as e:
        print(e)
        return json.dumps({'error': "Server error while adding message to convo.", 'code': 9})

