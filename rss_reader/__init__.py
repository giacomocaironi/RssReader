from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = "login"

from rss_reader import routes, models, errors, parser
from threading import Thread
import time
import logging
import os


def wait_print():
    while True:
        try:
            parser.parse_feeds()
        except:
            pass


# https://stackoverflow.com/questions/25504149/why-does-running-the-flask-dev-server-run-itself-twice
# if os.environ.get("WERKZEUG_RUN_MAIN") != "true":  # prevents double threads
#     logging.basicConfig(level=logging.INFO)
#     print(1)
#     Thread(target=wait_print, args=()).start()
#     print(1)
