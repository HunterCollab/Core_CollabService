
from flask import Blueprint, request
import api.AuthorizationAPI
from services.DBConn import db
from pprint import pprint
from datetime import datetime # Imported datetime to do the basic date functions.
import json

@collab_api.route("/createCollab", methods['POST']) # Create collaboration, post method
@api.AuthorizationAPI.requires_auth # Requires authentication beforehand
def create_collab():
    """"
        Function to create and upload new collaboration details
        """
    try:
        data = request.get_json()
        collabowner = request.usernameFromToken # By default, the owner of the collaboration is the submitting user.
        collabid = 0 # Need to write function to maintain collaboration document size.
        collabsize = data['size'] #  # Maximum size of the collaboration group. Should be more than 1.
        collabmembers = data['members'] # Current members of the collaboration. Owner is member by default.
            # Number of members cannot exceed size.
        collabdate = datetime.now().strftime(("%Y-%m-%d %H:%M:%S")) # Post date for the collaboration. Need to decide
            # format.
        # collabduration = # Duration of the collaboration. Probably a datetime.
        # collabexpiration = # Expiration time for the collaboration. Probably a datetime.
        # collabstatus = # Bool. True is open, false is closed. Closed collaborations do not expire. Used for searches.
        collabtitle = data['title'] # Title of the collaboration. Sanitize.
        collabdescription = data['description'] # Description of the collaboration. Sanitize.
        collabclasses = data['classes'] # List of classes wanted. By default, empty.
        collabskills = data['skills'] # List of skills wanted. By default, empty.
        collabapplicants = data['applicants'] # Pending applicants to the collaboration. By default, empty.

        # There probably should be a way to find out if there's a duplicate collaboration.
        # If a collaboration has no members, it is deleted?
        # If a collaboration is closed, it stops being searchable as open.
        # Do collaborations expire if not fulfilled? Even if fulfilled for a long time?

        try:
            newcollab = { # Make a list with all the collaboration parameters.
                "_id" : collabid,
                'owner' : collabowner,
                'size' : collabsize,
                'members' : collabmembers,
                'date' : collabdate,
                'duration' : "",
                'expiration' : "",
                'status' : "",
                'title' : collabtitle,
                'description' : collabdescription,
                'classes' : collabclasses,
                'skills' : collabskills,
                'applicants' : collabapplicants
            }

            result = collabDB.insert_one(newcollab) # Upload that list to the server.

            if (result.inserted_id):
                print("New Collaboration: '" + collabtitle + "' created.")
                return json.dumps({ 'success' : true})

            else:
                return json.dumps({ 'error' : "Failed to upload new collaboration to database"})

        except:
            return "", 400

    except:
        return "", 500

@collab_api.route("/getCollabDetails", methods['GET'])
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
        # Assuming user profiles do not have a link of their collaborations, the database must be filtered based on if
            # the user is found as an active member in the collaboration data.
        data = collabDB.query.filter(collabDB.members.in_(username)).all() # This is supposed to filter by the elements
            # in the 'Member" list match the username of the querying user. Unsure if functional.
        if data is None:
            return json.dumps({'error': "No collaborations found for username: " + username})
        else:
            # I do not think sending the collaboration ID is important.
            print("Returned user collaborations: " + username)
            return json.dumps(data)
    except Exception as e:
        print(e)
        return json.dumps({'error': "Server error while checking user collaborations."})

@collab_api.route("/getAllCollabs", methods['GET'])
@api.AuthorizationAPI.requires_auth
def get_allcollab():
    '''
        Return all collaborations ever
        '''
    try:
        data = collabDB.collaborations
        return json.dumps(data)

    except:
        return "", 400