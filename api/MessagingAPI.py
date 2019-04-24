import time
import json
import security.JWT
import services.realtime.messaging.RealtimeServer as RealtimeServer

from flask import Blueprint, request
from services.data.DBConn import db
from bson.objectid import ObjectId
from bson import json_util

messaging_api = Blueprint('messaging_api', __name__)
convoDB = db.conversations
collabDB = db.collabs
userDB = db.users


current_milli_time = lambda: int(round(time.time() * 1000))


def getDisplayName(username): #TODO Cache this.
    record = userDB.find_one({'username': username}, {'name': 1})
    if record is None:
        return "UNKNOWN"
    else:
        return record['name']


def extract_time(json):
    try:
        # Also convert to int since update_time will be string.  When comparing
        # strings, "10" is smaller than "2".
        return int(json['messages'][0]['time'])
    except KeyError:
        return 0

@messaging_api.route("/myConvos", methods=['GET'])
@security.JWT.requires_auth
def getConvoList():
    username = request.userNameFromToken

    try:
        records = convoDB.find({'participants': username}, {'_id': 0, 'participants': 1, 'messages': {'$slice': 1}})
        convoList = list(records)

        for rec in convoList:
            u1 = rec['participants'][0]
            u2 = rec['participants'][1]
            rec['otherUser'] = ""
            if u1 == username:
                rec['otherUser'] = u2
            else:
                rec['otherUser'] = u1
            rec['title'] = getDisplayName(rec['otherUser'])

        collabRecs = collabDB.find({'members': username}, {'_id': 1, 'title': 1, 'messages': {'$slice': 1}})
        collabList = list(collabRecs)

        collabList.extend(convoList)

        for elem in collabList:
            if 'messages' in elem:
                for msg in elem['messages']:
                    msg['dispName'] = getDisplayName(msg['sender'])

        collabList.sort(key=extract_time, reverse=True)
        return json.dumps(collabList, default=json_util.default)
    except Exception as e:
        print(e)
        return json.dumps({'error': "Server error while pulling convos.", 'code': 9})


@messaging_api.route("/getMessages", methods=['POST'])
@security.JWT.requires_auth
def getMessages():
    username = request.userNameFromToken
    data = request.get_json()
    if not ('page' in data):
        return json.dumps({'error': "'page' not provided.", 'code': -1})
    if not (('otherUser' in data) or ('collabId' in data)):
        return json.dumps({'error': "'otherUser'/'collabId' not provided.", 'code': -2})

    page = data['page']
    participants = []
    collabId = False

    if 'collabId' in data:
        collabId = data['collabId']
    else:
        participants = [data['otherUser'], username]
        if not (len(participants) == 2):
            return json.dumps({'error': "More than 2 participants provided.", 'code': 48})

    records = []

    if collabId:
        records = collabDB.find({'_id': ObjectId(collabId)}, {'_id': 1, 'messages': {'$slice': [(20 * page), 20]}})
    else:
        records = convoDB.find({'participants': participants}, {'_id': 0, 'messages': {'$slice': [(20 * page), 20]}})

    listed = list(records)
    print(listed)

    for elem in listed:
        if 'messages' in elem:
            for msg in elem['messages']:
                msg['dispName'] = getDisplayName(msg['sender'])

    return json.dumps(listed, default=json_util.default)


@messaging_api.route("/sendMessage", methods=['POST'])
@security.JWT.requires_auth
def sendMessage():
    username = request.userNameFromToken
    data = request.get_json()
    if not ('message' in data):
        return json.dumps({'error': "'message' not provided.", 'code': -1})
    if not (('recipient' in data) or ('collabId' in data)):
        return json.dumps({'error': "'recipient'/'collabId' not provided.", 'code': -2})

    message = data['message']
    participants = []
    collabId = False

    if 'collabId' in data:
        collabId = data['collabId']
    else:
        participants = [data['recipient'], username]
        if not (len(participants) == 2):
            return json.dumps({'error': "More than 2 participants provided.", 'code': 48})

    if not collabId:
        try:
            record = convoDB.find_one({'participants': participants}, {'_id': 1})
            if record is None:  # Create conversation with all the participants
                newConvo = {
                    'participants': participants,
                    'messages': []
                }
                result = convoDB.insert_one(newConvo)  # Upload that list to the server.
                if not result.inserted_id:
                    return json.dumps({'error': "Failed to create new convo.", 'code': 1})
                # print("New convo created.")

        except Exception as e:
            print(e)
            return json.dumps({'error': "Server error while trying to create new convo.", 'code': -9})

    try:
        message = {'sender': username, 'message': message, 'time': current_milli_time()}
        if not collabId:
            convoDB.update({'participants': participants}, {'$push': {'messages': {'$each': [message], '$sort': {'time': -1}}}})
            RealtimeServer.getInstance().pingClients(participants)
        else:
            collabDB.update({'_id': ObjectId(collabId)},
                           {'$push': {'messages': {'$each': [message], '$sort': {'time': -1}}}})
            collabrec = collabDB.find_one({'_id': ObjectId(collabId)}, {'members': 1})
            if collabrec:
                RealtimeServer.getInstance().pingClients(collabrec['members'])
        return json.dumps({'success': True})
    except Exception as e:
        print(e)
        return json.dumps({'error': "Server error while adding message to convo.", 'code': 9})

