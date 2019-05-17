import security.JWT
import json

from flask import Blueprint, request
from services.data.DBConn import db
from bson import json_util  # Trying a PyMongo serializer
from bson.objectid import ObjectId
from pymongo import MongoClient
from collections import OrderedDict

client = MongoClient('mongodb://localhost:27017')

collab_api = Blueprint('collab_api', __name__)
collabDB = db.collabs


class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)


@collab_api.route("/createCollab", methods=['POST'])  # Create collaboration, post method
@security.JWT.requires_auth  # Requires authentication beforehand
def create_collab():
    """Endpoint to create new Collaborations. This endpoint requires the requesting user to be an authenticated user
    to properly function.

    Request Body Parameters:
        size: int, JSON, required
        date: int, JSON, required
        duration: int, JSON, required
        location: string, JSON, required
        title: string, JSON, required
        description: string, JSON, required
        classes: array of strings, JSON, required
        skills: array of strings, JSON, required

    This endpoint receives relevant Collaboration information from sent JSON object and uploads it as a Collaboration to
    the Collaboration database, returning True on success. If it does not receive sufficient or proper data, the
    creation fails and an appropriate error is returned.
        """
    data = request.get_json()
    try:
        newcollab = {
            'owner': request.userNameFromToken,
            'size': data['size'],
            'members': [request.userNameFromToken],
            'date': data['date'],
            'duration': data['duration'],
            'location': data['location'],
            'status': True,
            'title': data['title'],
            'description': data['description'],
            'classes': data['classes'],
            'skills': data['skills'],
            'applicants': [],
        }

        result = collabDB.insert_one(newcollab)

        if result.inserted_id:
            print("New Collaboration: '" + data['title'] + "' created.")
            return json.dumps({'success': True})
        else:
            return json.dumps({'error': "Failed to upload new collaboration to database", 'code': 64})
    except Exception as e:
        print(e)
        return json.dumps({'error': "Server error while making new collab.", 'code': 65})

@collab_api.route("/getCollabDetails", methods=['GET'])
@security.JWT.requires_auth
def get_collab():
    """Endpoint to return requesting user's Collaborations. This endpoint requires the requesting user to be
    authorized.

    Return: list of collaboration objects, JSON

    This endpoint reads the user's username and queries the database for any Collaborations the user is a member of. If
    any Collaborations are found, all are returned in a JSON object. If not, an appropriate message is returned. If
    the search fails, an appropriate error is returned.
        """
    username = request.args.get('username')
    if not username:
        username = request.userNameFromToken
    else:
        username = username.lower()

    try:
        record = collabDB.find({'members': {'$all': [username]}})
        if record is None:
            return json.dumps({'error': "No collaborations found for username", 'code': 65})
        else:
            doc_list = list(record)
            return json.dumps(doc_list, default=json_util.default)
    except Exception as e:
        print(e)
        return json.dumps({'error': "Server error while checking user collaborations.", 'code': 66})


@collab_api.route("/getAllCollabs", methods=['GET'])
@security.JWT.requires_auth
def get_all_collabs():
    """Endpoint to return all Collaborations in the database. This endpoint requires the requesting user to be
    authorized.

    Return: list of collaboration objects, JSON

    This endpoint queries the database for any existing Collaborations, active or inactive. If any Collaborations are
    found, all are returned in a JSON object. If not, an appropriate message is returned. If the search fails, an
    appropriate error is returned.
        """
    try:
        record = collabDB.find()
        if record is None:
            return json.dumps({'error': "No collaborations found", 'code': 69})
        else:
            doc_list = list(collabDB.find())
            return json.dumps(doc_list, default=json_util.default)
    except Exception as e:
        print(e)
        return json.dumps({'error': "While getting all collabs.", 'code' : 70})

@collab_api.route("/getActiveCollabs", methods = ['GET'])
@security.JWT.requires_auth
def get_all_active_collabs():
    """
    Endpoint to return all active Collaborations in the database. This endpoint requires the requesting user to be
    authorized.

    Return: list of collaboration objects, JSON

    This endpoint queries the database for any existing Collaborations set as active. If any Collaborations are found,
    all are returned in list of JSON objects. If not, an appropriate message is returned. If the search fails, an
    appropriate error is returned.
        """
    try:
        record = collabDB.find()
        if record is None:
            return json.dumps({'error': "No collaborations found", 'code' : 71})
        else:
            doc_list = list(collabDB.find({ 'status' : True}))
            return json.dumps(doc_list, default=json_util.default)
    except Exception as e:
        print(e)
        return json.dumps({'error': "Getting all active collabs.", 'code' : 72})

@collab_api.route("/deleteCollab", methods = ['POST'])
@security.JWT.requires_auth
def delete_collab() :
    """
    Endpoint to set a specified collaboration to inactive. This endpoint requires the requesting user to be
    authorized.

    Request Body Parameters:
        id: string, JSON, required

    This endpoint queries the database for the specified collaboration. If the collaboration is found, its "status"
    variable is set to False. If the search fails, an appropriate error message is returned.
        """
    try:
        data = request.get_json()
        collab_id = data['id']
        record = collabDB.find({'_id' : ObjectId(collab_id)})
        if record is None:
            return json.dumps({'error': "No collaborations matched id", 'code' : 996})
        else:
            try:
                result = collabDB.update_one(
                    {"_id": ObjectId(collab_id)},
                    {
                        "$set": {
                            "status": False,
                        }
                    }
                )
                if result.matched_count > 0:
                    return json.dumps({'success': True})
                else:
                    return json.dumps({'success': False, 'error': 'Updating collab data failed for some reason', 'code': 998})
            except Exception as e:
                print(e)
                return json.dumps({'error': "Error while trying to delete existing doc.", 'code' : 999})
    except Exception as e:
        print(e)
        return json.dumps({'error': "Server error finding doc to delete", 'code' : 997})

@collab_api.route("/deleteCollabForReal", methods = ['DELETE'])
@security.JWT.requires_auth
def delete_collab_for_real() :
    """
    Endpoint to remove a specified collaboration from the database. This endpoint requires the requesting user to be
    authorized.

    Request Body Parameters:
        id: string, JSON, required

    This endpoint queries the database for the specified collaboration. If the collaboration is found, it is removed
    from the database. If the search fails, an appropriate error message is returned.
        """
    try:
        data = request.get_json()
        collab_id = data['id']
        record = collabDB.find({'_id' : ObjectId(collab_id)})
        if record is None:
            return json.dumps({'error': "No collaborations matched id", 'code' : 996})
        else:
            try:
                collabDB.delete_one({'_id' : ObjectId(collab_id)})
                print(collab_id + " deleted!")
                doc_list = list(collabDB.find())
                return json.dumps(doc_list, default=json_util.default) #Uh, return the remaining list i guess
            except Exception as e:
                print(e)
                return json.dumps({'error': "Error while trying to delete existing doc.", 'code': 997})
    except Exception as e:
        print(e)
        return json.dumps({'error': "Server error finding doc to delete", 'code': 998})

@collab_api.route("/editCollab", methods = ['POST'])
@security.JWT.requires_auth
def edit_collab() :
    """
    Endpoint to edit a specified collaboration's member variables. This endpoint requires the requesting user to be an
    authenticated user to properly function.

    Request Body Parameters:
        id: string, JSON, required
        owner: string, JSON, optional
        size: int, JSON, optional
        members: array of strings, JSON, optional
        date: int, JSON, optional
        duration: int, JSON, optional
        location, string, JSON, optional
        status: bool, JSON, optional
        title: string, JSON, optional
        description: string, JSON, optional
        classes: array of strings, JSON, optional
        skills: array of strings, JSON, optional
        applicants: array of strings, JSON, optional

    This endpoint queries the database for the specified collaboration. If the collaboration is found, other variables
    included, if any, are updated. If the search fails, an appropriate error message is returned.
        """
    data = request.get_json()
    collab_id = data['id']
    record = collabDB.find({'_id' : ObjectId(collab_id)})
    if record is None:
        return json.dumps({'error': "No collaborations to update matched id", 'code': 996})
    else:
        try:
            if 'owner' in data and isinstance(data['owner'], str):
                record = collabDB.update_one(
                    {"_id": ObjectId(collab_id)},
                    {
                        "$set": {
                            "owner": data['owner']
                        }
                    }
                )
            if 'size' in data and isinstance(data['size'], int):
                record = collabDB.update_one(
                    {"_id": ObjectId(collab_id)},
                    {
                        "$set": {
                            "size": data['size']
                        }
                    }
                )
            if 'members' in data and isinstance(data['members'], list):
                record = collabDB.update_one(
                    {"_id": ObjectId(collab_id)},
                    {
                        "$set": {
                            "members": data['members']
                        }
                    }
                )
            if 'date' in data and isinstance(data['date'], int):
                record = collabDB.update_one(
                    {"_id": ObjectId(collab_id)},
                    {
                        "$set": {
                            "date": data['date']
                        }
                    }
                )
            if 'duration' in data and isinstance(data['duration'], int):
                record = collabDB.update_one(
                    {"_id": ObjectId(collab_id)},
                    {
                        "$set": {
                            "duration": data['duration']
                        }
                    }
                )
            if 'location' in data and isinstance(data['location'], str):
                record = collabDB.update_one(
                    {"_id": ObjectId(collab_id)},
                    {
                        "$set": {
                            "location": data['location']
                        }
                    }
                )
            if 'status' in data and isinstance(data['status'], bool):
                record = collabDB.update_one(
                    {"_id": ObjectId(collab_id)},
                    {
                        "$set": {
                            "status": data['status']
                        }
                    }
                )
            if 'title' in data and isinstance(data['title'], str):
                record = collabDB.update_one(
                    {"_id": ObjectId(collab_id)},
                    {
                        "$set": {
                            "title": data['title']
                        }
                    }
                )
            if 'description' in data and isinstance(data['description'], str):
                record = collabDB.update_one(
                    {"_id": ObjectId(collab_id)},
                    {
                        "$set": {
                            "description": data['description']
                        }
                    }
                )
            if 'classes' in data and isinstance(data['classes'], list):
                record = collabDB.update_one(
                    {"_id": ObjectId(collab_id)},
                    {
                        "$set": {
                            "classes": data['classes']
                        }
                    }
                )
            if 'skills' in data and isinstance(data['skills'], list):
                record = collabDB.update_one(
                    {"_id": ObjectId(collab_id)},
                    {
                        "$set": {
                            "skills": data['skills']
                        }
                    }
                )
            if 'applicants' in data and isinstance(data['applicants'], list):
                record = collabDB.update_one(
                    {"_id": ObjectId(collab_id)},
                    {
                        "$set": {
                            "applicants": data['applicants']
                        }
                    }
                )
            if record.modified_count > 0:
                return json.dumps({'success': True})
            else:
                return json.dumps({'success': True})
        except Exception as e:
            print(e)
            return json.dumps({'error': "Error while trying to update existing doc.", 'code': 997})

@collab_api.route("/joinCollab", methods = ['POST'])
@security.JWT.requires_auth
def join_collab() :
    """
    Endpoint to add the user to a non-full collaboration's members array. This endpoint requires the requesting user to
    be an authenticated user to properly function.

    Request Body Parameters:
        id: string, JSON, required

    This endpoint queries the database for the specified collaboration. If the collaboration is found and the size of its
    members array is less than the size specified, the user's name is added to the collaboration's members array. If the
    search fails, an appropriate error message is returned.
        """
    username = request.args.get('username')
    if not username:
        username = request.userNameFromToken
    else:
        username = username.lower()
    data = request.get_json()
    collab_id = data['id']

    record = collabDB.find_one(
            {'_id': ObjectId(collab_id)})
    if record is None:
        return json.dumps({'error': "No collaborations matched id", 'code': 996})
    if username in record["members"]:
        return json.dumps({'error': "Username is already member of id", 'code': 997})
    else:
        if len(record["members"]) >= record["size"]:
            return json.dumps({'error': "Members of collab full id", 'code': 998})
        else:
            try:
                result = collabDB.update_one(
                    {
                        "_id": ObjectId(collab_id),
                    },
                    {"$push" : {
                        "members" : username
                    }
                    }
                )
                if result.modified_count > 0:
                    return json.dumps({'success': True})
                else:
                    return json.dumps({'error': "joining collabs failed", 'code': 999})
            except Exception as e:
                print(e)
                return json.dumps({'error': "Error while trying to update existing doc.", 'code': 995})

@collab_api.route("/leaveCollab", methods = ['POST'])
@security.JWT.requires_auth
def leave_collab() :
    """
    Endpoint to remove the user from a specified collaboration's members array. This endpoint requires the requesting
    user to be an authorized.

    Request Body Parameters:
        id: string, JSON, required

    This endpoint queries the database for the specified collaboration. If the collaboration is found and the user is in
    the members array, the user is removed from the members array. If the user removed is the owner and the updated
    collaboration is not empty, the collaboration's owner is updated to be the next user in the members array. If the
    updated collaboration is empty, the collaboration is set to inactive. If the search fails, an appropriate error
    message is returned.
        """
    username = request.args.get('username')
    if not username:
        username = request.userNameFromToken
    else:
        username = username.lower()
    data = request.get_json()
    collab_id = data['id']
    record = collabDB.find_one({'_id': ObjectId(collab_id)})
    if record is None:
        return json.dumps({'error': "No collaborations update matched id", 'code': 995})
    if username not in record["members"]:
        return json.dumps({'error': "Username is not member of id", 'code': 996})
    else:
        if record["owner"] != username:
            try:
                result = collabDB.update_one(
                    {
                        "_id": ObjectId(collab_id)
                    },
                    {"$pull" : {
                        "members" : username
                    }
                    }
                )
                if result.modified_count > 0:
                    return json.dumps({'success': True})
                else:
                    return json.dumps({'error': "Error while trying to leave collab.", 'code': 997})
            except Exception as e:
                print(e)
                return json.dumps({'error': "Error while trying to leave collab.", 'code': 997})
        else:
            if len(record["members"]) <= 1:
                try:
                    result = collabDB.update_one(
                        {
                            "_id": ObjectId(collab_id)
                        },
                            {"$pull": {
                                "members": username
                            },
                            "$set": {
                                "owner": "",
                                "status": False
                            }
                            }
                    )
                    if result.modified_count > 0:
                        return json.dumps({'success': True})
                    else:
                        return json.dumps({'error': "Error while trying to leave collab.", 'code': 997})
                except Exception as e:
                    print(e)
                    return json.dumps({'error': "Error while trying to leave collab.", 'code': 997})
            else:
                newmembers = record["members"].remove(username)
                newowner = record["members"][0]
                try:
                    result = collabDB.update_one(
                        {
                            "_id": ObjectId(collab_id)
                        },
                        {"$set": {
                            "owner": newowner,
                        },
                        "$pull": {
                            "members": username
                        }
                        }
                    )
                    if result.modified_count > 0:
                        return json.dumps({'success': True})
                    else:
                        return json.dumps({'error': "Error while trying to leave collab.", 'code': 997})
                except Exception as e:
                    print(e)
                    return json.dumps({'error': "Error while trying to leave collab.", 'code': 997})

@collab_api.route("/getRecommendedCollabs", methods=['POST'])
@security.JWT.requires_auth
def recommend_collabs():
    """
    Endpoint to get a list of active collaborations user is not a member of that best fit user based on user's skills
    and classes. This endpoint requires the requesting user to be an authenticated user to properly function.

    Request Body Parameters:
        skills: array of strings, JSON, required
        classes: array of strings, JSON, required
    Return: list of collaboration objects, JSON

    This endpoint queries the database for active collaborations the user is not a member of. If collaborations are
    found, the server matches each of their listed skills and classes with the user's and scores them on the number that
    match. It then returns a list of JSON objects for up to three collaborations that scored the highest. If the search
    fails, an appropriate error message is returned.
        """
    username = request.args.get('username')
    if not username:
        username = request.userNameFromToken
    else:
        username = username.lower()
    record = request.get_json()

    scoredict = OrderedDict()
    scorelist = []
    for doc in collabDB.find({
        '$and' : [
            {'status' : True},
            {'members' : {'$nin' : [username]}}
        ]
    }):
        collabscore = 0
        for elem in record['skills']:
            if doc['skills'].count(elem):
                collabscore + 1
        for elem in record['classes']:
            if doc['classes'].count(elem):
                collabscore + 1
        scoredict.update({doc['_id'] : collabscore})
    sorted(scoredict.values(), reverse=True)
    slist = list(scoredict.keys())
    if len(slist) >= 3:
        for i in range(3):
            recommended = collabDB.find_one({'_id' : slist[0]})
            scorelist.append(recommended)
            del slist[0]
        return json.dumps(scorelist, default=json_util.default)
    else:
        for i in range(len(slist)):
            recommended = collabDB.find_one({'_id' : slist[0]})
            scorelist.append(recommended)
            del slist[0]
        return json.dumps(scorelist, default=json_util.default)

@collab_api.route("/getCollab", methods = ['POST'])
@security.JWT.requires_auth
def get_collab_by_id():
    """
    Endpoint to return a specified collaboration's details. This endpoint requires the requesting user to be an
    authenticated user to properly function.

    Request Body Parameters:
        id: string, JSON, required

    This endpoint queries the database for the specified collaboration. If the collaboration is found, its details are
    returned as a JSON object. If the search fails, an appropriate error message is returned.
        """
    data = request.get_json()
    collab_id = data['id']

    try:
        record = collabDB.find({'_id': ObjectId(collab_id)})
        if record is None:
            return json.dumps({'error': "No collaborations found", 'code': 69})
        else:
            doc_list = list(collabDB.find({'_id': ObjectId(collab_id)}))
            return json.dumps(doc_list, default=json_util.default)
    except Exception as e:
        print(e)
        return json.dumps({'error': "Getting collab", 'code' : 70})


