from flask import Blueprint, request
import api.AuthorizationAPI
from services.DBConn import db
import time # Imported time to do the basic date functions.
from bson import json_util  # Trying a PyMongo serializer
from bson.objectid import ObjectId
import json
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
@api.AuthorizationAPI.requires_auth  # Requires authentication beforehand
def create_collab():
    """"
        Function to create and upload new collaboration details
        """

    data = request.get_json()
    try:
        collabowner = request.userNameFromToken # By default, the owner of the collaboration is the submitting user.
        collabsize = data['size'] #  # Maximum size of the collaboration group. Should be more than 1.
        collabmembers = [request.userNameFromToken] # Current members of the collaboration. Owner is member by default.
            # Number of members cannot exceed size.
        collabdate = data['date'] # Post date for the collaboration. In milliseconds
        collabduration = data['duration']
        collabloc = data['location']
        collabstatus = True # Bool. True is open, false is closed. Closed collaborations do not expire. Used for searches.
        collabtitle = data['title'] # Title of the collaboration. Sanitize.
        collabdescription = data['description'] # Description of the collaboration. Sanitize.
        collabclasses = data['classes'] # List of classes wanted. By default, empty.
        collabskills = data['skills'] # List of skills wanted. By default, empty.
        collabapplicants = [] # Pending applicants to the collaboration. By default, empty.

        # There probably should be a way to find out if there's a duplicate collaboration.
        # If a collaboration has no members, it is deleted?
        # If a collaboration is closed, it stops being searchable as open.
        # Do collaborations expire if not fulfilled? Even if fulfilled for a long time?
        # Do we need the ability to have collaborations be closed and invite only?

        try:
            newcollab = { # Make a list with all the collaboration parameters.
                'owner' : collabowner,
                'size' : collabsize,
                'members' : collabmembers,
                'date' : collabdate,
                'duration' : collabduration,
                'location' : collabloc,
                'status' : True,
                'title' : collabtitle,
                'description' : collabdescription,
                'classes' : collabclasses,
                'skills' : collabskills,
                'applicants' : collabapplicants,
            }

            result = collabDB.insert_one(newcollab)  # Upload that list to the server.

            if result.inserted_id:
                print("New Collaboration: '" + collabtitle + "' created.")
                return json.dumps({'success': True})
            else:
                return json.dumps({'error': "Failed to upload new collaboration to database2", 'code': 64})

        except Exception as e:
            print(e)
            return json.dumps({'error': "Server error while making new collab in try block.", 'code': 65})

    except Exception as e:
        print(e)
        return json.dumps({'error': "Server error while making new collab.", 'code': 66})


@collab_api.route("/getCollabDetails", methods=['GET'])
@api.AuthorizationAPI.requires_auth
def get_collab():
    """
        Function to return user's collaborations
        """
    username = request.args.get('username')
    if not username:
        username = request.userNameFromToken
    else:
        username = username.lower()

    try:
        record = collabDB.find({'members': {'$all': [username]}})
        if record is None:
            return json.dumps({'error': "No collaborations found for username: " + username})
        else:
            print("returned collab details: ")
            doc_list = list(record)
            return json.dumps(doc_list, default=json_util.default)
    except Exception as e:
        print(e)
        return json.dumps({'error': "Server error while checking user collaborations."})


@collab_api.route("/getAllCollabs", methods=['GET'])
@api.AuthorizationAPI.requires_auth
def get_all_collabs():
    '''
        Return all active collaborations
        '''
    try:
        record = collabDB.find()
        if record is None:
            return json.dumps({'error': "No collaborations found"})
        else:
            print("returned collab details: ")
            doc_list = list(collabDB.find())
            return json.dumps(doc_list, default=json_util.default)

    except Exception as e:
        print(e)
        return json.dumps({'error': "Getting all collabs.", 'code' : 70})

@collab_api.route("/getActiveCollabs", methods = ['GET'])
@api.AuthorizationAPI.requires_auth
def get_all_active_collabs():
    '''
        Return all active collaborations
        '''
    try:
        record = collabDB.find()
        if record is None:
            return json.dumps({'error': "No collaborations found"})
        else:
            print("returned collab details: ")
            doc_list = list(collabDB.find({ 'status' : True}))
            return json.dumps(doc_list, default=json_util.default)

    except Exception as e:
        print(e)
        return json.dumps({'error': "Getting all active collabs.", 'code' : 70})

@collab_api.route("/deleteCollab", methods = ['POST'])
@api.AuthorizationAPI.requires_auth
def delete_collab() : # Take teh collaboration _ID and
    # Verify if user is owner first THIS HAS NOT BEEN DONE YET
    # Make sure collab exists in first try block
    # Attempt to delete in second try block
    try:
        data = request.get_json()
        # collabowner = request.userNameFromToken # make sure the person trying to delete is the collab owner first
        # maybe make a server delete function with different credentials later
        collab_id = data['id'] #  Get the collab id from the Json i guess?
        # I'm assuming that the app is passing back a JSON object with just the collaboration id in it
        # nvm the simpler way is to pass it as a string
        record = collabDB.find({'_id' : ObjectId(collab_id)})
        # The problem now is that this is not firing the None
        # It's going to the else statement even when the collab_id is not in the database
        if record is None:
            return json.dumps({'error': "No collaborations matched _id: " + collab_id})
        else:
            # attempt to delete
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
                return json.dumps({'error': "Error while trying to delete existing doc."})
    except Exception as e:
        print(e)
        return json.dumps({'error': "Server error finding doc to delete"})

# Edit collabs
@collab_api.route("/deleteCollabForReal", methods = ['DELETE'])
@api.AuthorizationAPI.requires_auth
def delete_collab_for_real() : # Take teh collaboration _ID and
    # Verify if user is owner first THIS HAS NOT BEEN DONE YET
    # Make sure collab exists in first try block
    # Attempt to delete in second try block
    try:
        data = request.get_json()
        # collabowner = request.userNameFromToken # make sure the person trying to delete is the collab owner first
        # maybe make a server delete function with different credentials later
        collab_id = data['id'] #  Get the collab id from the Json i guess?
        # I'm assuming that the app is passing back a JSON object with just the collaboration id in it
        # nvm the simpler way is to pass it as a string
        record = collabDB.find({'_id' : ObjectId(collab_id)})
        # The problem now is that this is not firing the None
        # It's going to the else statement even when the collab_id is not in the database
        if record is None:
            return json.dumps({'error': "No collaborations matched _id: " + collab_id})
        else:
            # attempt to delete
            try:
                collabDB.delete_one({'_id' : ObjectId(collab_id)})
                print(collab_id + " deleted!")
                doc_list = list(collabDB.find())
                return json.dumps(doc_list, default=json_util.default) #Uh, return the remaining list i guess
            except Exception as e:
                print(e)
                return json.dumps({'error': "Error while trying to delete existing doc."})
    except Exception as e:
        print(e)
        return json.dumps({'error': "Server error finding doc to delete"})

@collab_api.route("/editCollab", methods = ['POST'])
@api.AuthorizationAPI.requires_auth
def edit_collab() :
    data = request.get_json()
    # Somehow get the collab id from the json
    # put a try block here
    collab_id = data['id'] #id is passed from the APP
    # Link the collab id to the actual object
    record = collabDB.find({'_id' : ObjectId(collab_id)}) # Out of all collabs, find the one with the matching id
    # Im going to assume that, because this is built on updating a previous collab, that there are real default values
    if record is None:
        return json.dumps({'error': "No collaborations to update matched _id: " + collab_id})
    else:
        # attempt to update
        try:
            if 'owner' in data and isinstance(data['owner'], str):
                record = collabDB.update_one(
                    {"_id": ObjectId(collab_id)},
                    {
                        "$set": {
                            "owner": data['owner']
                            # Remember that owners should only be set to people who are also members
                        }
                    }
                )
            if 'size' in data and isinstance(data['size'], int):
                record = collabDB.update_one(
                    {"_id": ObjectId(collab_id)},
                    {
                        "$set": {
                            "size": data['size']
                            # Remember that owners should only be set to people who are also members
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
                            "date": data['size']
                        }
                    }
                )
            if 'duration' in data and isinstance(data['duration'], int):
                record = collabDB.update_one(
                    {"_id": ObjectId(collab_id)},
                    {
                        "$set": {
                            "duration": data['duration']
                            # Remember that owners should only be set to people who are also members
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
                            # Remember that owners should only be set to people who are also members
                        }
                    }
                )
            if 'title' in data and isinstance(data['title'], str):
                record = collabDB.update_one(
                    {"_id": ObjectId(collab_id)},
                    {
                        "$set": {
                            "title": data['title']
                            # Remember title should not be empty
                        }
                    }
                )
            if 'description' in data and isinstance(data['description'], str):
                record = collabDB.update_one(
                    {"_id": ObjectId(collab_id)},
                    {
                        "$set": {
                            "description": data['description']
                            # Remember that owners should only be set to people who are also members
                        }
                    }
                )
            if 'classes' in data and isinstance(data['classes'], list):
                record = collabDB.update_one(
                    {"_id": ObjectId(collab_id)},
                    {
                        "$set": {
                            "classes": data['classes']
                            # Remember that owners should only be set to people who are also members
                        }
                    }
                )
            if 'skills' in data and isinstance(data['skills'], list):
                record = collabDB.update_one(
                    {"_id": ObjectId(collab_id)},
                    {
                        "$set": {
                            "skills": data['skills']
                            # Remember that owners should only be set to people who are also members
                        }
                    }
                )
            if 'applicants' in data and isinstance(data['applicants'], list):
                record = collabDB.update_one(
                    {"_id": ObjectId(collab_id)},
                    {
                        "$set": {
                            "applicants": data['applicants']
                            # Remember that owners should only be set to people who are also members
                        }
                    }
                )
            if record.modified_count > 0:
                return json.dumps({'success': True})
            else:
                return json.dumps({'error': "Updating collabs failed})
        except Exception as e:
            print(e)
            return json.dumps({'error': "Error while trying to update existing doc."})

# In search API, need a filter collabs changed to check

@collab_api.route("/joinCollab", methods = ['POST'])
@api.AuthorizationAPI.requires_auth
def join_collab() :
    username = request.args.get('username')
    if not username:
        username = request.userNameFromToken
    else:
        username = username.lower()
    data = request.get_json()
    collab_id = data['id']
    record = collabDB.find_one(
            {'_id': ObjectId(collab_id)})
    # okay so this works. now maybe these should separate.
    if record is None:
        return json.dumps({'error': "No collaborations matched _id: " + collab_id})
    # Now we have the collab in "record". This is a dict
    if username in record["members"]: # If the username is in the members list, end
        return json.dumps({'error': "Username is already member of _id: " + collab_id})
    else:
        if len(record["members"]) >= record["size"]:
            return json.dumps({'error': "Members of collab full _id: " + collab_id})
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
                    json.dumps({'error': "joining collabs failed})
            except Exception as e:
                print(e)
                return json.dumps({'error': "Error while trying to update existing doc."})

@collab_api.route("/leaveCollab", methods = ['POST'])
@api.AuthorizationAPI.requires_auth
def leave_collab() :
    # Retrieve a username variable from the username token
    username = request.args.get('username')
    if not username:
        username = request.userNameFromToken
    else:
        username = username.lower()
    # Get the data from the JSON body
    data = request.get_json()
    collab_id = data['id']
    # Make sure the collaboration with the matching _id exists
    record = collabDB.find_one({'_id': ObjectId(collab_id)})
    if record is None:
        return json.dumps({'error': "No collaborations update matched _id: " + collab_id})
    # Make sure that collaboration has the user as a member
    if username not in record["members"]:  # If the user is not in members array, end
        return json.dumps({'error': "Username is not member of _id: " + collab_id})
    else: # So user is member of collab
        # Also need to change owner
        if record["owner"] != username: # If owner is not username, size > 1. Just remove the user.
            try:
                # Remove the user from member array
                result = collabDB.update_one(
                    {
                        "_id": ObjectId(collab_id)
                    },
                    {"$pull" : {
                        "members" : username
                    }
                    }
                )
                if result.modified_count > 0: # On success,
                    return json.dumps({'success': True})
                else:
                    return json.dumps({'error': "Error while trying to leave collab."})
            except Exception as e:
                print(e)
                return json.dumps({'error': "Error while trying to leave collab."})
        else: # If the owner is the user, then problems.
            # Two cases, owner must shift, or collab must be archived
            # Case 1, ownership shifts to next person
            if len(record["members"]) <= 1: # If the owner was the only person in the collab
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
                    if result.modified_count > 0:  # On success,
                        return json.dumps({'success': True})
                    else:
                        return json.dumps({'error': "Error while trying to leave collab."})
                except Exception as e:
                    print(e)
                    return json.dumps({'error': "Error while trying to leave collab."})
            else: # If the user was not only member, set user to new members array
                newmembers = record["members"].remove(username) # remove user from members array
                newowner = record["members"][0]  # Set new owner to be first element of members array
                try:
                    result = collabDB.update_one(
                        {
                            "_id": ObjectId(collab_id)
                        },
                        {"$set": {
                            "owner": newowner,
                            "members": newmembers
                        }
                        }
                    )
                    if result.modified_count > 0:  # On success,
                        return json.dumps({'success': True})
                    else:
                        return json.dumps({'error': "Error while trying to leave collab."})
                except Exception as e:
                    print(e)
                    return json.dumps({'error': "Error while trying to leave collab."})

# Recommend collabs
@collab_api.route("/getRecommendedCollabs", methods = ['GET'])
@api.AuthorizationAPI.requires_auth
def recommend_collabs() :
    record = request.get_json()

    scoredict = OrderedDict()
    scorelist = []
    # iterate through the collabs, match the skills and classes and input to list
    for doc in collabDB.find({'status': True}):
        collabscore = 0
        for elem in record['skills']:
            if doc['skills'].count(elem): # there is at least one match in skills, increment
                collabscore + 1
        for elem in record['classes']:
            if doc['classes'].count(elem):
                collabscore + 1
        scoredict.update({doc['_id'] : collabscore})
    # sort the dict, then output the first 5 with highest score
    sorted(scoredict.values(), reverse=True)
    slist = list(scoredict.keys())
    # make a dict with _id and score? then sort by score and return _ids?
    if len(slist) >= 5:
        for i in range(5):
            # Actually, I need to get teh _id, then pop the dict, then find the id and append it to the list
            recommended = collabDB.find_one({'_id' : slist[0]})
            scorelist.append(recommended)
            del slist[0]
        return json.dumps(scorelist, default=json_util.default)
    else:
        for i in range(len(slist)):
            # Actually, I need to get teh _id, then pop the dict, then find the id and append it to the list
            recommended = collabDB.find_one({'_id' : slist[0]})
            scorelist.append(recommended)
            del slist[0]
        return json.dumps(scorelist, default=json_util.default) # Should I be worried this can return an empty list?

# Get user classes and skills from JSON
# parse and compare with all active collabs
# put into sorted array and output at random from the first few

