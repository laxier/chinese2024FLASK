from flask import Flask
from config import Config
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bootstrap import Bootstrap5
import os
import json

app = Flask(__name__)

app = Flask(__name__, static_folder=os.path.join(os.getcwd(), 'static'))
app.config.from_object(Config)

bootstrap = Bootstrap5(app)
moment = Moment(app)

db = SQLAlchemy(app)

login = LoginManager(app)
login.login_view = 'login'


@app.template_filter('from_json')
def from_json(json_string):
    """Convert a JSON string to a Python object."""
    try:
        return json.loads(json_string)
    except json.JSONDecodeError:
        return []


from app import routes, models
