from flask import Blueprint, request
import api.AuthorizationAPI
from services.DBConn import db
from pprint import pprint
import json

collab_api = Blueprint('collab_api', __name__)
collabDB = db.collaborations

@collab_api.route("/createCollab")
@api.AuthorizationAPI.requires_auth
def createCollab():
    #Impletement createCollab.
    #Get all the details from the body of the request and then
    #collabDB.insert()
    #{ title = "", creator=request.userNameFromToken }
    return request.userNameFromToken + "Hello World from the Collaboration API"