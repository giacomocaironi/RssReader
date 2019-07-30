from rss_reader import db, login
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

from hashlib import md5


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


feeds = db.Table(
    "feeds",
    db.Column("follower_id", db.Integer, db.ForeignKey("user.id")),
    db.Column("feed_id", db.Integer, db.ForeignKey("rss_feed.id")),
)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(128), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    feeds = db.relationship(
        "RssFeed", secondary=feeds, lazy="dynamic", backref="followers"
    )

    def get_feed_entries(self):  # to improve
        if len(self.feeds.all()) == 0:
            return []
        first_entry = self.feeds.all()[0].posts
        entries = []
        for entry in self.feeds.all()[1:]:
            entries.append(entry.posts)
        entries = first_entry.union(*entries)
        return entries.order_by(RssEntry.date.desc())

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_following(self, rss_feed):
        return rss_feed in self.feeds

    def __repr__(self):
        return "<User {}>".format(self.username)


def get_site_from_link(link):
    divided_link = link.split("/")
    result = divided_link[0] + "//" + divided_link[2]
    return result


class RssFeed(db.Model):
    __searchable__ = ["title"]
    title = db.Column(db.String(128))
    id = db.Column(db.Integer, primary_key=True)
    link = db.Column(db.String(128), unique=True)
    posts = db.relationship("RssEntry", backref="feed_file", lazy="dynamic")

    def get_favicon(self):
        return get_site_from_link(self.link) + "/favicon.ico"

    def __repr__(self):
        return self.title


class RssEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    href = db.Column(
        db.String(128)
    )  # unique is not false to let multiple feed files have the same article
    feed_id = db.Column(db.ForeignKey("rss_feed.id"))
    title = db.Column(db.String(128))
    date = db.Column(db.DateTime, index=True)
    content = db.Column(db.String(1024))  # I will cut every entry
