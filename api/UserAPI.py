import os
import io
import security.JWT
import json
import boto3
import time
import hashlib

from flask import Blueprint, request, send_file, Response
from services.data.DBConn import db
from bson import Binary

user_api = Blueprint('user_api', __name__)
userDB = db.users


@user_api.route("", methods=['PUT'])
def createUser():
    """
    Endpoint to create a new user using specified username and password.

    Request Body Parameters:
        username : string, JSON, required
        password : string, JSON, required

    Queries the database to see if there is already a user with this username. If not, creates a new user this username
    and password and default settings. If the process fails, an appropriate error message is returned.
        """
    username = request.args.get('username')
    password = request.args.get('password')

    if not username:
        return json.dumps({'error': "Username parameter was not provided.", 'code': 1})
    if not password:
        return json.dumps({'error': "Password parameter was not provided.", 'code': 2})

    username = username.lower()
    if "@" not in username:
        return json.dumps({'error': "Username is not a valid email.", 'code': 3})
    if username[-18:] != "@myhunter.cuny.edu":
        return json.dumps({'error': "Email is not a valid @myhunter.cuny.edu email.", 'code': 4})
    if username[:-18] == "":
        return json.dumps({'error': "@myhunter.cuny.edu email is invalid.", 'code': 5})

    if len(password) < 6 or len(password) > 52:
        return json.dumps({'error': "Password must be at least 6 characters and less than 52 characters long.", 'code': 6})

    salt = os.urandom(32).hex()
    hashy = hashlib.sha512()
    hashy.update(('%s%s' % (salt, password)).encode('utf-8'))
    hashed_password = hashy.hexdigest()

    try:
        record = userDB.find_one({'username': username}, {'_id': 1})
        if record is None:
            user = {'username': username, 'salt': salt, 'password': hashed_password, 'name': username, 'github': '', 'linkedin': '', 'skills': [],
                    'classes': [], 'profilePicture': None}
            result = userDB.insert_one(user)
            if result.inserted_id:
                # print("created new user: " + username)
                authtoken = security.JWT.encode_auth_token(username).decode("utf-8")
                return json.dumps({'success': True, 'token': authtoken})
            else:
                return json.dumps({'error': "Server error while creating new user.", 'code': 7})
        else:
            return json.dumps({'error': "User already exists.", 'code': 8})
    except Exception as e:
        print(e)
        return json.dumps({'error': "Server error while checking if username already exists.", 'code': 9})


@user_api.route("/", methods=['GET'], defaults={'username': None})
@user_api.route("/<username>", methods=['GET'])
@security.JWT.requires_auth
def getUserDetails(username):
    """
    Endpoint to get user details for a specified user, defaulting to the current user. This endpoint requires the
    requesting user to be authorized.

    URL Parameters:
          username: string, optional
    Return: user object, JSON

    This endpoint queries the database for the user based on the current user's username. If the user is found in the
    database, the user's details are returned in JSON format. If the process fails, an appropriate error message is
    returned.
         """
    if not username:
        username = request.userNameFromToken
    else:
        username = username.lower()

    try:
        record = userDB.find_one({'username': username}, {'username': 1, 'name': 1, 'github': 1, 'linkedin': 1, 'skills': 1, 'classes': 1, 'profilePicture': 1})
        if record is None:
            return json.dumps({'error': "No user details found for username: " + username})
        else:
            del record['_id']  # don't send document id
            # del record['password'] #don't send the password
            # print("returned user details: " + username)
            return json.dumps(record)
    except Exception as e:
        print(e)
        return json.dumps({'error': "Server error while checking if username already exists."})


@user_api.route("/skills", methods=['GET'], defaults={'username': None})
@user_api.route("/skills/<username>", methods=['GET'])
@security.JWT.requires_auth
def getSkills(username):
    """
    Endpoint to get skills for a specified user, defaulting to the user. This endpoint requires the requesting user to
    be an authorized.

    URL Parameters:
        username: string, optional
    Return: array of strings, JSON

    This endpoint queries the database for the user based on the specified username or, if blank, the current user's
    username. If the user is found in the database, the user's skills are returned in JSON format. If the search fails,
    an appropriate error message is returned.
        """
    if not username:
        username = request.userNameFromToken
    else:
        username = username.lower()

    try:
        record = userDB.find_one({'username': username}, {'skills': 1})
        if record is None:
            return json.dumps({'error': "No user details found for username: " + username})
        else:
            del record['_id']  # don't send document id
            # del record['password'] #don't send the password
            # print("returned user skills: " + username)
            return json.dumps(record)
    except Exception as e:
        print(e)
        return json.dumps({'error': "Server error while checking if username already exists."})


@user_api.route("/classes", methods=['GET'], defaults={'username': None})
@user_api.route("/classes/<username>", methods=['GET'])
@security.JWT.requires_auth
def getClasses(username):
    """
    Endpoint to get classes for a specified user, defaulting to the user. This endpoint requires the requesting user to
    be an authorized.

    URL Parameters:
        username: string, optional
    Return: array of strings, JSON

    This endpoint queries the database for the user based on the specified username or, if blank, the current user's
    username. If the user is found in the database, the user's classes are returned in JSON format. If the search fails,
    an appropriate error message is returned.
        """
    if not username:
        username = request.userNameFromToken
    else:
        username = username.lower()

    try:
        record = userDB.find_one({'username': username}, {'classes': 1})
        if record is None:
            return json.dumps({'error': "No user details found for username: " + username})
        else:
            del record['_id']  # don't send document id
            # del record['password'] #don't send the password
            # print("returned user skills: " + username)
            return json.dumps(record)
    except Exception as e:
        print(e)
        return json.dumps({'error': "Server error while checking if username already exists."})


def skillClassValidityChecker(data):
    """
    :param data: arry of strings
    :return: bool
    """
    if isinstance(data, list):
        for elem in data:
            if not isinstance(elem, str):
                return False
    else:
        return False
    return True

@user_api.route("", methods=['POST'])
@security.JWT.requires_auth
def updateUserDetails():
    """
    Endpoint to update user details for the current user. This endpoint requires the requesting user to be authorized.

    Request Body Parameters:
        name: string, JSON, optional
        github: string, JSON, optional
        linkedin: string, JSON, optional
        skills: array of strings, JSON, optional
        classes: array of strings, JSON, optional

    This endpoint queries the database for the user based on the current user's username. If the user is found in the
    database, the user's details are set according to the specified fields. If the search fails, an appropriate error
    message is returned.
         """
    content = request.get_json()
    username = request.userNameFromToken
    # print(content)

    if 'name' in content and isinstance(content['name'], str):
        res = userDB.update_one(
            {"username": username},
            {
                "$set": {
                    "name": content['name'],
                }
            }
        )

    if 'github' in content and isinstance(content['github'], str):
        res = userDB.update_one(
            {"username": username},
            {
                "$set": {
                    "github": content['github'],
                }
            }
        )

    if 'linkedin' in content and isinstance(content['linkedin'], str):
        res = userDB.update_one(
            {"username": username},
            {
                "$set": {
                    "linkedin": content['linkedin'],
                }
            }
        )

    if 'skills' in content and skillClassValidityChecker(content['skills']):
        res = userDB.update_one(
            {"username": username},
            {
                "$set": {
                    "skills": content['skills'],
                }
            }
        )

    if 'classes' in content and skillClassValidityChecker(content['classes']):
        res = userDB.update_one(
            {"username": username},
            {
                "$set": {
                    "classes": content['classes'],
                }
            }
        )

    return json.dumps({'success': True})


@user_api.route("/skills", methods=['POST'])
@security.JWT.requires_auth
def updateSkills():
    """
    Endpoint to update skills for the current user. This endpoint requires the requesting user to be authorized.

    Request Body Parameters:
        skills: array of strings, JSON, required

    This endpoint queries the database for the user based on the current user's username. If the user is found in the
    database, the user's skills are set according to the specified fields. If the search fails, an appropriate error
    message is returned.
       """
    content = request.get_json()
    # print(content)

    if not ('skills' in content):
        return json.dumps({'error': "'skills' not provided.", 'code': 1})

    if not (skillClassValidityChecker(content['skills'])):
        return json.dumps({'error': "'skills' is not a valid array.", 'code': 2})

    username = request.userNameFromToken

    try:
        record = userDB.find_one({'username': username}, {'_id': 1, 'skills': 1})
        if record is None:
            return json.dumps({'error': "No user details found for username: " + username})
        else:
            result = userDB.update_one(
                {"username": username},
                {
                    "$set": {
                        "skills": content['skills']
                    }
                }
            )
            if result.matched_count > 0:
                return json.dumps({'success': True})
            else:
                return json.dumps({'success': False, 'error': 'Updating user data failed for some reason', 'code': 998})
    except Exception as e:
        print(e)
        return json.dumps({'error': "Server error while trying to find user.", 'code': 999})


@user_api.route("/classes", methods=['POST'])
@security.JWT.requires_auth
def updateClasses():
    """
    Endpoint to update classes for the current user. This endpoint requires the requesting user to be authorized.

    Request Body Parameters:
        classes: array of strings, JSON, required

    This endpoint queries the database for the user based on the current user's username. If the user is found in the
    database, the user's classes are set according to the specified fields. If the search fails, an appropriate error
    message is returned.
         """
    content = request.get_json()
    # print(content)

    if not ('classes' in content):
        return json.dumps({'error': "'classes' not provided.", 'code': 1})

    if not (skillClassValidityChecker(content['classes'])):
        return json.dumps({'error': "'classes' is not a valid array.", 'code': 2})

    username = request.userNameFromToken

    try:
        record = userDB.find_one({'username': username}, {'_id': 1, 'classes': 1})
        if record is None:
            return json.dumps({'error': "No user details found for username: " + username})
        else:
            result = userDB.update_one(
                {"username": username},
                {
                    "$set": {
                        "classes": content['classes']
                    }
                }
            )
            if result.matched_count > 0:
                return json.dumps({'success': True})
            else:
                return json.dumps({'success': False, 'error': 'Updating user data failed for some reason', 'code': 998})
    except Exception as e:
        print(e)
        return json.dumps({'error': "Server error while trying to find user.", 'code': 999})


@user_api.route("/profilePicture", methods=['GET'])
@security.JWT.requires_auth
def getUserPicture():
    """
    Endpoint to access the profile picture for the current user. This endpoint requires the requesting user to be
    authorized.

    This endpoint queries the database for the user based on the current user's username. If the user is found in the
    database and the user has set a profile picture, the user's profile picture image is fetched from the CloudFront
    database. If the search fails, an appropriate error message is returned.
       """
    username = request.args.get('username')
    if not username:
        username = request.userNameFromToken
    else:
        username = username.lower()

    try:
        record = userDB.find_one({'username': username}, {'profilePicture': 1})
        if record is None:
            return Response(status=404)
        else:
            if 'profilePicture' in record and record['profilePicture'] is not None:
                return "dkdno63yk5s4u.cloudfront.net/" + record['profilePicture']
               # return send_file(io.BytesIO(record['profilePicture']), attachment_filename='ppic_' + username, mimetype='image/png')
            else:
                return Response(status=404)
    except Exception as e:
        print(e)
        return json.dumps({'error': "Server error while fetching profile picture", 'code': 1})


@user_api.route("/profilePicture", methods=['POST'])
@security.JWT.requires_auth
def updateUserPicture():
    """
    Endpoint to update the profile picture for the current user. This endpoint requires the requesting user to be
    authorized.

    Request Body Parameters:
        pic: image, JSON, required

    This endpoint queries the database for the user based on the current user's username. If the user is found in the
    database, the server uploads the new picture to the database and updates the user's profile picture to that file.
    If the search fails, an appropriate error message is returned.
            """
    username = request.userNameFromToken
    file = request.files['pic']
    if not file:
        return json.dumps({'error': "No file uploaded with identifier 'pic'", 'code': 1})

    if not file.content_type.startswith("image/"):
        return json.dumps({'error': "File is not an image.", 'code': 842})

    length = 0
    if length > (1000000 * 5):
        return json.dumps({'error': "File too large.", 'code': 3})

    try:
        record = userDB.find_one({'username': username}, {'profilePicture': 1, '_id': 1})
        if record is None:
            return json.dumps({'error': "No user found for username: " + username})
        else:
            s3client = boto3.client('s3')
            timeNow = str(round(time.time() * 1000))

            key = username + "/" + timeNow + "/" + file.filename
            s3client.upload_fileobj(file, 'barterplace', key,
                                    ExtraArgs={'ACL': 'public-read', 'ContentType': file.content_type})

            result = userDB.update_one(
                {"username": username},
                {
                    "$set": {
                        "profilePicture": key
                    }
                }
            )
            if result.matched_count > 0:
                return json.dumps({'success': True})
            else:
                return json.dumps({'error': 'Updating user profile picture failed for some reason', 'code': 998})
    except Exception as e:
        print(e)
        return json.dumps({'error': "Server error while updating profile picture", 'code': 2})
