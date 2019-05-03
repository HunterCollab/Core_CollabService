import security.JWT
import threading
import json
import time
from threading import Timer
from flask import Blueprint, request
from services.data.DBConn import db

search_api = Blueprint('search_api', __name__)
userDB = db.users
classesDB = db.classes

allDistinctSkills = None
allDistinctClasses = None
allPresetClasses = []

classesPreset = classesDB.find({'major': 'CSCI'})
classesList = list(classesPreset)
for cls in classesList:
    toAdd = cls['major'] + ' ' + str(cls['number'])[:3] + " - " + cls['title']
    #print(toAdd)
    allPresetClasses.append(toAdd)


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


def purgeLoop():
    global allDistinctSkills
    global allDistinctClasses

    print("[Skill Cache] Purging ...")
    allDistinctSkills = userDB.distinct("skills")

    print("[Class Cache] Purging ...")
    allDistinctClasses = userDB.distinct("classes")

    allDistinctClasses = allDistinctClasses + allPresetClasses

    # allDistinctSkills.sort();
    # allDistinctClasses.sort();

    try:
        Timer(60.0 * 5, purgeLoop).start()
    except (KeyboardInterrupt, SystemExit):
        print("EXCEPT")


try:
    thread = threading.Thread(target=purgeLoop(), args=())
    thread.daemon = True
    thread.start()
    time.sleep(3)
except (KeyboardInterrupt, SystemExit):
    print("EXCEPT")
