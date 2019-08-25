import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = os.environ.get("SECRET_KEY") or "hgdk;4lAgjadkls;AEGs"
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL"
    ) or "sqlite:///" + os.path.join(basedir, "app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    POSTS_PER_PAGE_INDEX = 5
    LOG_TO_STDOUT = os.environ.get("LOG_TO_STDOUT")
    REMEMBER_COOKIE_HTTPONLY = True
    # whoosh config
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    WHOOSH_BASE = "fulltextindex"
    ADMINS = [os.environ.get("ADMIN") or None]
