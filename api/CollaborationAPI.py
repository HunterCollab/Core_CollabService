
from flask import Blueprint, request, jsonify
import api.AuthorizationAPI
from services.DBConn import db
from pprint import pprint
from datetime import datetime # Imported datetime to do the basic date functions.
from bson import json_util # Trying a pymongo serializer
import json
import pymongo
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017')

collab_api = Blueprint('collab_api', __name__)
collabDB = db.collabs

class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)

@collab_api.route("/createCollab", methods = ['POST']) # Create collaboration, post method
@api.AuthorizationAPI.requires_auth # Requires authentication beforehand
def create_collab():
    """"
        Function to create and upload new collaboration details
        """

    data = request.get_json()
    print(data)
    try:
        collabowner = request.userNameFromToken # By default, the owner of the collaboration is the submitting user.
        collabid = 0 # Should be a unique ID for each entry
        collabsize = data['size'] #  # Maximum size of the collaboration group. Should be more than 1.
        collabmembers = [request.userNameFromToken] # Current members of the collaboration. Owner is member by default.
            # Number of members cannot exceed size.
        collabdate = datetime.now() # Post date for the collaboration. Need to decide
            # format.
        # collabduration = # Duration of the collaboration. Probably a datetime.
        # collabexpiration = # Expiration time for the collaboration. Probably a datetime.
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
                "id" : collabid,
                'owner' : collabowner,
                'size' : collabsize,
                'members' : collabmembers,
                'date' : collabdate,
                'duration' : "",
                'expiration' : "",
                'status' : True,
                'title' : collabtitle,
                'description' : collabdescription,
                'classes' : collabclasses,
                'skills' : collabskills,
                'applicants' : collabapplicants
            }

            result = collabDB.insert_one(newcollab) # Upload that list to the server.

            if (result.inserted_id):
                print("New Collaboration: '" + collabtitle + "' created.")
                return json.dumps({ 'success' : True})

            else:
                return json.dumps({ 'error' : "Failed to upload new collaboration to database", 'code': 64})


        except Exception as e:
            print(e)
            return json.dumps({'error': "Server error while making new collab in try block.", 'code': 65})

    except Exception as e:
        print(e)
        return json.dumps({'error': "Server error while making new collab.", 'code': 66})

@collab_api.route("/getCollabDetails", methods = ['GET'])
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
        record = collabDB.find({ 'members': { '$all': [ username ] } })
        if record is None:
            return json.dumps({'error': "No collaborations found for username: " + username})
        else:
            print("returned collab details: ")
            doc_list = list(record)
            return json.dumps(doc_list, default=json_util.default)
    except Exception as e:
        print(e)
        return json.dumps({'error': "Server error while checking user collaborations."})

@collab_api.route("/getAllCollabs", methods = ['GET'])
@api.AuthorizationAPI.requires_auth
def get_allcollab():
    '''
        Return all collaborations ever
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



# Need a delete collab function
@collab_api.route("/getAllCollabs", methods = ['DELETE'])
@api.AuthorizationAPI.requires_auth
def delete_collab(collabid) : # Take teh collaboration ID and
    pass

# Edit collabs

# In search API, need a filter collabs