from flask import Flask
from flask_cors import CORS

# Initialize the app
app = Flask(__name__, instance_relative_config=True)
cors = CORS(app)
app.config["CORS_HEADERS"] = "Content-Type"

# pylint: disable=import-error,wrong-import-position
from anagrammer import views
