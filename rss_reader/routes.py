from rss_reader import app, db
from flask import render_template, flash, redirect, url_for, request
from rss_reader.models import User, RssEntry, RssFeed
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from rss_reader.forms import LoginForm, RegistrationForm, AddRssForm

# from datetime import datetime
import requests
import feedparser

# from html.parser import HTMLParser
from dateutil import parser
from lxml.html.clean import clean_html

# from .rss_test import parse_file, parse_feeds

from requests_futures.sessions import FuturesSession


def parse_file(link):
    data = requests.get(link).text  # get rss file location
    return feedparser.parse(data)  # parse and return rss file


def parse_feeds():
    session = FuturesSession()
    feeds = RssFeed.query.all()
    urls = []
    for feed in feeds:
        urls.append(feed.link)
    responses = []
    for url in urls:
        responses.append(session.get(url))
    for i in range(len(urls)):
        feed = feeds[i]
        data = responses[i].result()
        add_new_entries(feedparser.parse(data.text), feed)


def add_new_entries(data, feed):
    for entry in data.entries:
        time = parser.parse(entry.updated)
        try:
            content = clean_html(entry.summary[:500])
            entry_db = RssEntry(
                title=entry.title,
                date=time,
                feed_id=feed.id,
                content=content,
                href=entry.link,
            )
            db.session.add(entry_db)
            db.session.commit()
        except:
            db.session.rollback()


@app.before_request
def before_request():
    pass


@app.route("/")
@login_required
def index():
    feeds = current_user.get_feed_entries()
    feed_length = len(feeds)
    return render_template("index.html", feeds=feeds, length=feed_length)


@app.route("/feed/<feed_id>")
@login_required
def feed(feed_id):
    feed = RssFeed.query.filter_by(id=feed_id).first_or_404()
    entries = feed.posts.all()
    return render_template("feed.html", feeds=entries, title=feed.title, feed=feed)


@app.route("/update")
def update():
    parse_feeds()
    return redirect(url_for("index"))


@app.route("/explore")
@login_required
def explore():
    feeds = RssFeed.query.all()
    return render_template("explore.html", feeds=feeds)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(
            form.password.data
        ):  # can validate also in the form itself
            flash("invalid username or password")
            return redirect(url_for("login"))
        login_user(user, remember=form.remember_me.data)
        destination = request.args.get("next")
        if not destination or url_parse(destination).netloc != "":
            return redirect(url_for("index"))
        return redirect(destination)
    return render_template("login.html", form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("register.html", form=form)


@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    form = AddRssForm()
    if form.validate_on_submit():
        try:
            data = parse_file(form.rss_link.data)
            try:  # prevent doubles
                new_feed = RssFeed(title=data.feed.title, link=form.rss_link.data)
                db.session.add(new_feed)
                db.session.commit()
            except:
                db.session.rollback()
            try:
                current_user.feeds.append(new_feed)
                db.session.commit()
            except:
                db.session.rollback()
            try:
                add_new_entries(data, new_feed)
            except:
                db.session.rollback()
        except:
            db.session.rollback()
        return redirect(url_for("add"))
    return render_template("add.html", form=form)


@app.route("/follow/<rss_feed>")
@login_required
def follow(rss_feed):
    feed = RssFeed.query.filter_by(id=rss_feed).first_or_404()
    if feed in current_user.feeds:
        flash("you are already following this feed")
        return redirect(url_for("explore"))
    if feed is None:
        flash("the rss feed title is invalid")
        return redirect(url_for("explore"))
    current_user.feeds.append(feed)
    db.session.commit()
    return redirect(url_for("explore"))


@app.route("/unfollow/<rss_feed>")
@login_required
def unfollow(rss_feed):
    feed = RssFeed.query.filter_by(id=rss_feed).first_or_404()
    if feed not in current_user.feeds:
        flash("you are not following this feed")
        return redirect(url_for("explore"))
    if feed is None:
        flash("the rss feed title is invalid")
        return redirect(url_for("explore"))
    current_user.feeds.remove(feed)
    db.session.commit()
    return redirect(url_for("explore"))
