import os
from flask import Flask
from api.AuthorizationAPI import auth_api
from api.UserAPI import user_api

app = Flask(__name__)
app.register_blueprint(user_api, url_prefix='/user')
app.register_blueprint(auth_api, url_prefix='/auth')

@app.route("/")
def helloWorld():
  return "Welcome to the Hunter Collab API. There's nothing to see here."

if __name__ == "__main__":
	port = int(os.environ.get("PORT", 5000))
	app.run(host="0.0.0.0", port=port, threaded=True)