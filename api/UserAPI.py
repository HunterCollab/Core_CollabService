import io
from flask import Blueprint, request, send_file, Response
import api.AuthorizationAPI
from services.DBConn import db
from pprint import pprint
from bson import Binary
import json

user_api = Blueprint('user_api', __name__)
userDB = db.users

@user_api.route("/createUser")
def createUser():
    username = request.args.get('username')
    if not username: return json.dumps({ 'error': "Username parameter was not provided.", 'code': 1 })
    password = request.args.get('password')
    if not password: return json.dumps({ 'error': "Password parameter was not provided.", 'code': 2 })
    if "@" not in username: return json.dumps({ 'error': "Username is not a valid email.", 'code': 3 })
    
    username = username.lower()
    if (username[-18:] != "@myhunter.cuny.edu"): return json.dumps({ 'error': "Email is not a valid @myhunter.cuny.edu email.", 'code': 4 })
    if (username[:-18] == ""): return json.dumps({ 'error': "@myhunter.cuny.edu email is invalid.", 'code': 5 })
    
    passLength = len(password)
    if (passLength < 6 or passLength > 52): return json.dumps({ 'error': "Password must be at least 6 characters and less than 52 characters long.", 'code': 6 })
    
    QUERY = {'username': username}
    try:
        record = userDB.find_one(QUERY, { '_id': 1 })
        if record is None:
            user = { 'username': username, 'password': password, 'github': '', 'linkedin': '', 'skills': [], 'classes': [], 'profilePicture': None }
            result = userDB.insert_one(user)
            if (result.inserted_id):
                print("created new user: " + username)
                return json.dumps({ 'success': True })
            else:
                return json.dumps({ 'error': "Server error while creating new user.", 'code': 7 })
        else:
            return json.dumps({ 'error': "User already exists.", 'code': 8 })
    except:
        return json.dumps({ 'error': "Server error while checking if username already exists.", 'code': 9 })

@user_api.route("/getUserDetails")
@api.AuthorizationAPI.requires_auth
def getUserDetails():
    username = request.args.get('username')
    if not username:
        username = request.userNameFromToken
    else:
        username = username.lower()
    
    QUERY = {'username': username}
    try:
        record = userDB.find_one(QUERY, { '_id': 1, 'github': 1, 'linkedin': 1, 'skills': 1, 'classes': 1 })
        if record is None:
            return json.dumps({ 'error': "No user details found for username: " + username })
        else:
            del record['_id'] #don't send document id
            del record['password'] #don't send the password
            print("returned user details: " + username)
            return json.dumps(record)
    except Exception as e:
        print(e)
        return json.dumps({ 'error': "Server error while checking if username already exists." })

@user_api.route("/updateUserDetails", methods=['POST'])
@api.AuthorizationAPI.requires_auth
def updateUserDetails():
    content = request.get_json()
    print (content)
    if not ('github' in content and 'linkedin' in content and 'skills' in content and 'classes' in content):
        return json.dumps({ 'error': "The required four variables were not provided.", 'code': 1 })
    if not (isinstance(content['skills'], list) and isinstance(content['classes'], list)):
        return json.dumps({ 'error': "'skills' and 'classes' are not arrays.", 'code': 2 })
    if not (isinstance(content['github'], str) and isinstance(content['linkedin'], str)):
        return json.dumps({ 'error': "'github' and 'linkedin' are not strings", 'code': 3 })
    username = request.userNameFromToken
    QUERY = {'username': username}
    try:
        record = userDB.find_one(QUERY, { '_id': 1, 'github': 1, 'linkedin': 1, 'skills': 1, 'classes': 1 })
        if record is None:
            return json.dumps({ 'error': "No user details found for username: " + username })
        else:
            result = userDB.update_one(
                {"username": username},
                {
                    "$set": {
                        "github":content['github'],
                        "linkedin":content['linkedin'],
                        "skills":content['skills'],
                        "classes":content['classes']
                    }
                }
            )
            if result.matched_count > 0:
                return json.dumps({ 'success': True })
            else:
                return json.dumps({ 'success': False, 'error': 'Updating user data failed for some reason', 'code': 998 })
    except Exception as e:
        print(e)
        return json.dumps({ 'error': "Server error while trying to find user.", 'code': 999 })

    return 'Needds to be removed never come here'


@user_api.route("/getUserPicture")
@api.AuthorizationAPI.requires_auth
def getUserPicture():
    username = request.args.get('username')
    if not username:
        username = request.userNameFromToken
    else:
        username = username.lower()
    
    QUERY = {'username': username}
    try:
        record = userDB.find_one(QUERY, { 'profilePicture': 1 })
        if record is None:
            return Response(status=404)
        else:
            if 'profilePicture' in record and record['profilePicture'] is not None:
                return send_file(io.BytesIO(record['profilePicture']), attachment_filename='ppic_' + username, mimetype='image/png')
            else:
                return Response(status=404)
    except Exception as e:
        print(e)
        return json.dumps({ 'error': "Server error while fetching profile picture", 'code': 1 })

@user_api.route("/updateUserPicture", methods=['POST'])
@api.AuthorizationAPI.requires_auth
def updateUserPicture():
    username = request.userNameFromToken
    filee = request.files['pic'].read()
    if not (filee):
        return json.dumps({ 'error': "No file uploaded with identifier 'pic'", 'code': 1 })
    print(len(filee))
    if len(filee) > 1000000 : return json.dumps({ 'error': "File too large.", 'code': 3 })
    
    QUERY = {'username': username}
    try:
        record = userDB.find_one(QUERY, { 'profilePicture': 1, '_id': 1 })
        if record is None:
            return json.dumps({ 'error': "No user found for username: " + username })
        else:
            result = userDB.update_one(
                {"username": username},
                {
                    "$set": {
                        "profilePicture": Binary(filee)
                    }
                }
            )
            if result.matched_count > 0:
                return json.dumps({ 'success': True })
            else:
                return json.dumps({ 'error': 'Updating user profile picture failed for some reason', 'code': 998 })
    except Exception as e:
        print(e)
        return json.dumps({ 'error': "Server error while updating profile picture", 'code': 2 })