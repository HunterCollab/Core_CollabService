from flask import Blueprint, request
import api.AuthorizationAPI
from services.DBConn import db
import json

search_api = Blueprint('search_api', __name__)
userDB = db.users

allDistinctSkills = None
allDistinctClasses = None


@search_api.route("/skills")
@api.AuthorizationAPI.requires_auth
def searchSkills():
    query = request.args.get('query').lower()
    ret = [];
    for skill in allDistinctSkills:
        if (query in skill.lower()): ret.append(skill)
    return json.dumps({'matches': ret})


@search_api.route("/classes")
@api.AuthorizationAPI.requires_auth
def searchClasses():
    query = request.args.get('query').lower()
    ret = [];
    for classs in allDistinctClasses:
        if (query in classs.lower()): ret.append(classs)
    return json.dumps({'matches': ret})


import threading


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


f_stop = threading.Event()
# start calling f now and every 60 sec thereafter
f(f_stop)

# stop the thread when needed
# f_stop.set()
