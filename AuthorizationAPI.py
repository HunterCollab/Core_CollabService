import os
import jwt
import json
import datetime
from flask import Blueprint
from functools import wraps
from flask import request, Response

auth_api = Blueprint('auth_api', __name__)

#/auth/login?username=[]&password=[]
@auth_api.route("/login")
def login():
    username = request.args.get("username")
    password = request.args.get("password")
    if (username == "admin" and password == "admin"):
        authtoken = encode_auth_token(user_id = 1).decode("utf-8") 
        print (authtoken)
        return json.dumps({ 'token': authtoken })
    else:
        return json.dumps({ 'error': 'Invalid Credentials' })


#generates an encrypted auth token using the secret key valid for 600 seconds
def encode_auth_token(user_id):
    SECRET_KEY = b'-\x1c\x9b\xa7x\xacH\nE{\x85=\xa6\x0e[\xe2\xe3\xb2\x01D\xc4\xd2x\x0f'
    try:
        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=0, seconds=600),
            'iat': datetime.datetime.utcnow(),
            'userid': user_id
        }
        return jwt.encode(
            payload,
            SECRET_KEY,
            algorithm='HS256'
        )
    except Exception as e:
        return e

#Decodes the auth token and returns userid as integer if token is valid or else an error as a string
def decode_auth_token(auth_token):
    try:
        payload = jwt.decode(auth_token, SECRET_KEY)
        return payload['userid']
    except jwt.ExpiredSignatureError:
        return 'Signature expired. Please log in again.'
    except jwt.InvalidTokenError:
        return 'Invalid token. Please log in again.'

#Defines the @requires_auth decoration. Any endpoint with the decoration requires authentication
def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_token = request.cookies.get('capstoneAuth')
        if not auth_token: #Authtoken no present so send 401
            return Response('Missing Auth Token!\n' 'You have to login with proper credentials', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})
        
        user_id = decode_auth_token(auth_token) #Get userid from authtoken

        if type(user_id) is str: #if user_id is not an integer, it's an error, so send 401 with the error
            return Response(user_id+ '\n' 'You have to login with proper credentials', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})
        
        #set the userIdFromAuth var so user can be identified form the request
        request.userIdFromAuth = user_id 

        #send control back to actual endpoint function
        return f(*args, **kwargs)
    return decorated