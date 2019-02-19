from flask import Blueprint, request
import api.AuthorizationAPI
from services.DBConn import db
from pprint import pprint
import json

user_api = Blueprint('user_api', __name__)
userDB = db.users

@user_api.route("/")
@api.AuthorizationAPI.requires_auth
def userApiHelloWorld():
    return request.userNameFromToken + "Hello World from the User API"

@user_api.route("/createUser")
def createUser():
    username = request.args.get('username')
    if not username: return json.dumps({ 'success': False, 'error': "Username parameter was not provided." })
    password = request.args.get('password')
    if not password: return json.dumps({ 'success': False, 'error': "Password parameter was not provided." })
    
    if "@" not in username: return json.dumps({ 'success': False, 'error': "Username is not a valid email." })
    
    username = username.lower()
    if (username[-18:] != "@myhunter.cuny.edu"): return json.dumps({ 'success': False, 'error': "Email is not a valid @myhunter.cuny.edu email." })

    if (username[:-18] == ""): return json.dumps({ 'success': False, 'error': "@myhunter.cuny.edu email is invalid." })
    
    passLength = len(password)
    if (passLength < 6 or passLength > 52): return json.dumps({ 'success': False, 'error': "Password must be at least 6 characters and less than 52 characters long." })
    
    QUERY = {'username': username}
    try:
        record = userDB.find_one(QUERY)
        if record is None:
            user = { 'username': username, 'password': password }
            result = userDB.insert_one(user)
            if (result.inserted_id):
                return json.dumps({ 'success': True })
            else:
                return json.dumps({ 'success': False, 'error': "Server error while creating new user." })
        else:
            return json.dumps({ 'success': False, 'error': "User already exists." })
    except:
        return json.dumps({ 'success': False, 'error': "Server error while checking if username already exists." })
    
    
    return "Hello World from the createUser endpoint"