from flask import Flask
from config import Config
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bootstrap import Bootstrap5
import os

app = Flask(__name__)

app = Flask(__name__, static_folder=os.path.join(os.getcwd(), 'static'))
app.config.from_object(Config)

bootstrap = Bootstrap5(app)
moment = Moment(app)

db = SQLAlchemy(app)

login = LoginManager(app)
login.login_view = 'login'

from app import routes, models
