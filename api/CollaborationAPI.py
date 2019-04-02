from flask import Blueprint, request
import api.AuthorizationAPI
from services.DBConn import db
import time # Imported time to do the basic date functions.
from bson import json_util  # Trying a PyMongo serializer
from bson.objectid import ObjectId
import json
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017')

collab_api = Blueprint('collab_api', __name__)
collabDB = db.collabs

def collabRecAlgo(): # Algorithm to determine user recommended collabs. Takes user skills/classes and compares them
    # to all collabs
    pass

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
                #"id" : collabid, # In theory, mongodb is already creating this for us
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
                'applicants' : collabapplicants
            }

            result = collabDB.insert_one(newcollab)  # Upload that list to the server.

            if result.inserted_id:
                print("New Collaboration: '" + collabtitle + "' created.")
                return json.dumps({'success': True})
            else:
                return json.dumps({'error': "Failed to upload new collaboration to database", 'code': 64})

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
    details = json.dumps(request.get_json())
    if record is None: # This probably doesn't work right now. ignore
        return json.dumps({'error': "No collaborations update matched _id: " + collab_id})
    else:
        # attempt to update
        try:
            result = collabDB.update_one(
                    {"_id": ObjectId(collab_id)},
                    {
                        # probably need one layer of sanitation to make sure things like titles are not empty
                        "$set": {
                            "owner" : data['owner'],
                            "size" : data['size'],
                            "members" : data['members'],
                            "date" : data['date'],
                            "duration" : data['duration'],
                            "location" : data['location'],
                            "status" : data['status'],
                            "title" : data['title'], # Cannot be empty, but I think front end will sanitize this
                            "description" : data['description'],
                            "classes" : data['classes'],
                            "skills" : data['skills'],
                            "applicants" : data['applicants']
                        }
                    }
                )
            if result.modified_count > 0:
                return json.dumps({'success': True})
            else:
                return json.dumps(
                    {'success': False, 'error': 'Updating collab data failed for some reason', 'code': 998})
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
    if record is None:  # This probably doesn't work right now. ignore
        return json.dumps({'error': "No collaborations matched _id: " + collab_id})
    record = collabDB.find_one({
        "$and" : [
            {'_id': ObjectId(collab_id)},
            {'members': {"$nin": [username]}}
        ]
    })
    if record is None:
        return json.dumps({'error': "Username is already member of _id: " + collab_id})
    record = collabDB.find_one({
        "$and": [
            {'_id': ObjectId(collab_id)},
            {'members': {"$nin": [username]}},
            {'members': {"$size": {"$lt": 'size'}}}
        ]
    })
    if record is None:
        return json.dumps({'error': "Members of collab full _id: " + collab_id})
    else:
        # Retrieve the id of the collab, find it, and then add the user to it
        # if the user is in the members list already, break.

        # Okay, so now try to add the member to the id, checking for size and duplicate
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
                return json.dumps(
                    {'success': False, 'error': 'Updating collab members failed for some reason', 'code': 998})
        except Exception as e:
            print(e)
            return json.dumps({'error': "Error while trying to update existing doc."})

@collab_api.route("/leaveCollab", methods = ['POST'])
@api.AuthorizationAPI.requires_auth
def leave_collab() :
    username = request.args.get('username')
    if not username:
        username = request.userNameFromToken
    else:
        username = username.lower()
    data = request.get_json()
    collab_id = data['id']
    record = collabDB.find_one({'_id': ObjectId(collab_id)})  # Out of all collabs, find the one with the matching id
    if record is None:  # This probably doesn't work right now. ignore
        return json.dumps({'error': "No collaborations update matched _id: " + collab_id})
    record = collabDB.find_one(
        {"$and": [
            {"_id": ObjectId(collab_id)},
            {'members': {"$in": [username]}}
        ]}
    )
    if record is None:
        return json.dumps({'error': "No collaborations with matched _id: " + collab_id + " with user as member"})
    else:
        # Retrieve the id of the collab, find it, and then remove the user from it
        # Also need to change owner
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
                print("hello0")
                record = collabDB.find_one(
                    {"$and": [
                        {"_id": ObjectId(collab_id)},
                        {'members': {"$size": 0}}
                    ]
                    })
                if record is None:
                    return json.dumps({'success': True})
                else:
                    collabDB.update_one(
                        {"$and": [
                            {"_id": ObjectId(collab_id)},
                            {'members': {"$size": 0}}
                        ]
                        },
                        {"$set": {
                            "status": False
                        }})
                    return json.dumps({'success': "Collaboration has no members, so it was archived"})
            else:
                return json.dumps(
                    {'success': False, 'error': 'Removing collab members failed for some reason', 'code': 998})
        except Exception as e:
            print(e)
            return json.dumps({'error': "Error while trying to update existing doc."})





# Recommend collabs
@collab_api.route("/getRecommendedCollabs", methods = ['GET'])
@api.AuthorizationAPI.requires_auth
def recommend_collabs() :
    data = request.get_json() # This includes the class and skills arrays
    # Alternatively, can figure out user from username and then retrieve skills and classes
    classes = data['classes']
    skills = data['skills']
    collabRecAlgo(classes, skills)

    pass

def collabRecAlgo(classes, skills): # Algorithm to determine user recommended collabs. Takes user skills/classes and compares them
    # to all collabs
    # Gets a score based on matches
    # Add the scores together to make a priority queue
    # 
    pass

# Get user classes and skills from JSON
# parse and compare with all active collabs
# put into sorted array and output at random from the first few

