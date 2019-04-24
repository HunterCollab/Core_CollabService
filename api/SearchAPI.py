import security.JWT
import threading
import json

from flask import Blueprint, request
from services.data.DBConn import db

search_api = Blueprint('search_api', __name__)
userDB = db.users

allDistinctSkills = None
allDistinctClasses = None


@search_api.route("/skills", methods=['GET'])
@security.JWT.requires_auth
def searchSkills():
    query = request.args.get('query').lower()
    ret = []
    for skill in allDistinctSkills:
        if query in skill.lower():
            ret.append(skill)
    return json.dumps({'matches': ret})


@search_api.route("/classes", methods=['GET'])
@security.JWT.requires_auth
def searchClasses():
    query = request.args.get('query').lower()
    ret = []
    for _class in allDistinctClasses:
        if query in _class.lower():
            ret.append(_class)
    return json.dumps({'matches': ret})


def purgeLoop(plThread):
    global allDistinctSkills
    global allDistinctClasses

    print("[Skill Cache] Purging ...")
    allDistinctSkills = userDB.distinct("skills")

    print("[Class Cache] Purging ...")
    allDistinctClasses = userDB.distinct("classes")

    # allDistinctSkills.sort();
    # allDistinctClasses.sort();

    if not plThread.is_set():
        # call f() again in 5 mins
        threading.Timer(60 * 5, purgeLoop, [plThread]).start()


plThread = threading.Event()
try:
    purgeLoop(plThread)
except (KeyboardInterrupt, SystemExit):
    print("EXCEPT")
    plThread.set()
