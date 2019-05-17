import os
import services.realtime.messaging.RealtimeServer as RealtimeServer
from flask import Flask
from api.AuthorizationAPI import auth_api
from api.UserAPI import user_api
from api.CollaborationAPI import collab_api
from api.SearchAPI import search_api
from api.MessagingAPI import messaging_api
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.register_blueprint(user_api, url_prefix='/user') #All endpoints in UserAPI.py are prefixed with the /user route.
app.register_blueprint(auth_api, url_prefix='/auth') #All endpoints in Authorization.py are prefixed with the /auth route.
app.register_blueprint(collab_api, url_prefix='/collab') #All endpoints in CollaborationAPI.py are prefixed with the /collab route.
app.register_blueprint(search_api, url_prefix='/search') #All endpoints in SearhAPI.py are prefixed with the /search route.
app.register_blueprint(messaging_api, url_prefix='/messaging') #All endpoints in MessagingAPI.py are prefixed with the /messaging route.


# Root
@app.route("/", methods=['GET'])
def helloWorld():
    return "Welcome to the Hunter Collab API. There's nothing to see here."


if __name__ == "__main__":
    RealtimeServer.getInstance()  # Start the Realtime-Messaging Server
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, threaded=True)
