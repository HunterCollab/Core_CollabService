from flask import Blueprint, request
import api.AuthorizationAPI
from services.DBConn import db
import threading
import json

search_api = Blueprint('search_api', __name__)
userDB = db.users

allDistinctSkills = None
allDistinctClasses = None


@search_api.route("/skills", methods=['GET'])
@api.AuthorizationAPI.requires_auth
def searchSkills():
    query = request.args.get('query').lower()
    ret = []
    for skill in allDistinctSkills:
        if query in skill.lower():
            ret.append(skill)
    return json.dumps({'matches': ret})


@search_api.route("/classes", methods=['GET'])
@api.AuthorizationAPI.requires_auth
def searchClasses():
    query = request.args.get('query').lower()
    ret = []
    for _class in allDistinctClasses:
        if query in _class.lower():
            ret.append(_class)
    return json.dumps({'matches': ret})


def f(f_stop):
    global allDistinctSkills
    global allDistinctClasses
    print("Fetching all avaliable skills in the database...")
    allDistinctSkills = userDB.distinct("skills")
    # allDistinctSkills.sort();
    print("Fetching all avaliable classes in the database...")
    allDistinctClasses = userDB.distinct("classes")
    # allDistinctClasses.sort();
    if not f_stop.is_set():
        # call f() again in 5 mins
        threading.Timer(60 * 5, f, [f_stop]).start()


# start calling skill & class updates.
f(threading.Event())

# stop the thread when needed
# f_stop.set()
