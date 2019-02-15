from flask import Blueprint
from AuthorizationAPI import auth_api
import AuthorizationAPI

user_api = Blueprint('user_api', __name__)

@user_api.route("/")
@AuthorizationAPI.requires_auth
def userApiHelloWorld():
    return "Hello World from the user api"