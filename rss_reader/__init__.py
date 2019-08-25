from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_admin import Admin

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = "login"
admin_app = Admin(app, name="Jack rss reader", template_mode="bootstrap3")

from rss_reader import routes, models, errors, parser, admin
from flask_admin.contrib.sqla import ModelView
