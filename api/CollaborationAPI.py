from flask import Blueprint, request
import api.AuthorizationAPI
from services.DBConn import db
from pprint import pprint
import json

collab_api = Blueprint('collab_api', __name__)
collabDB = db.collaborations

@collab_api.route("/")
@api.AuthorizationAPI.requires_auth
def userApiHelloWorld():
    return request.userNameFromToken + "Hello World from the Collaboration API"