from flask import Blueprint, request
import api.AuthorizationAPI
from services.DBConn import db
from pprint import pprint
import json

user_api = Blueprint('user_api', __name__)
userDB = db.users

@user_api.route("/createUser")
def createUser():
    username = request.args.get('username')
    if not username: return json.dumps({ 'error': "Username parameter was not provided." })
    password = request.args.get('password')
    if not password: return json.dumps({ 'error': "Password parameter was not provided." })
    if "@" not in username: return json.dumps({ 'error': "Username is not a valid email." })
    
    username = username.lower()
    if (username[-18:] != "@myhunter.cuny.edu"): return json.dumps({ 'error': "Email is not a valid @myhunter.cuny.edu email." })
    if (username[:-18] == ""): return json.dumps({ 'error': "@myhunter.cuny.edu email is invalid." })
    
    passLength = len(password)
    if (passLength < 6 or passLength > 52): return json.dumps({ 'error': "Password must be at least 6 characters and less than 52 characters long." })
    
    QUERY = {'username': username}
    try:
        record = userDB.find_one(QUERY)
        if record is None:
            user = { 'username': username, 'password': password }
            result = userDB.insert_one(user)
            if (result.inserted_id):
                return json.dumps({ 'success': True })
            else:
                return json.dumps({ 'error': "Server error while creating new user." })
        else:
            return json.dumps({ 'error': "User already exists." })
    except:
        return json.dumps({ 'error': "Server error while checking if username already exists." })
    
    
    return "Hello World from the createUser endpoint"

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
        record = userDB.find_one(QUERY)
        if record is None:
            return json.dumps({ 'error': "No user details found for username: " + username })
        else:
            del record['_id']
            return json.dumps(record)
    except Exception as e:
        print(e)
        return json.dumps({ 'error': "Server error while checking if username already exists." })