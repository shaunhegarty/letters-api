from flask import Flask

# Initialize the app
app = Flask(__name__, instance_relative_config=True)

# pylint: disable=import-error,wrong-import-position
from anagrammer import views
