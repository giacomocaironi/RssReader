from rss_reader import app, db
from flask import render_template, flash, redirect, url_for, request
from rss_reader.models import User, RssEntry, RssFeed
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from rss_reader.forms import (
    LoginForm,
    RegistrationForm,
    AddRssForm,
    SearchForm,
    AdminModifyFeedForm,
)
from rss_reader.parser import (
    parse_file,
    parse_feeds,
    add_new_entries,
    get_site_from_link,
)


@app.before_request
def before_request():
    pass


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    page = request.args.get("page", 1, type=int)
    feeds = current_user.get_feed_entries()
    if feeds != []:
        feeds = feeds.paginate(page, 25, False)
        next_url = url_for("index", page=feeds.next_num) if feeds.has_next else None
        prev_url = url_for("index", page=feeds.prev_num) if feeds.has_prev else None
        return render_template(
            "index.html", feeds=feeds.items, prev_url=prev_url, next_url=next_url
        )
    else:
        return render_template("index.html", feeds=[], prev_url=None, next_url=None)


@app.route("/feed/<feed_id>")
@login_required
def feed(feed_id):
    feed = RssFeed.query.filter_by(id=feed_id).first_or_404()
    entries = feed.posts.order_by(RssEntry.date.desc())
    return render_template("feed.html", feeds=entries, title=feed.title, feed=feed)


# @app.route("/update")
# def update():
#     parse_feeds()
#     return redirect(url_for("index"))


@app.route("/explore")
@login_required
def explore():
    question = request.args.get("q", "", type=str)
    form = SearchForm()
    if form.validate_on_submit():
        question = form.q.data
    if question:
        # feeds = RssFeed.query.filter(RssFeed.title.contains(question)).all()
        feeds = (
            RssFeed.query.filter(RssFeed.title.ilike("%{}%".format(question)))
            .limit(10)
            .all()
        )
        # feeds = RssFeed.query.whoosh_search(question).all()
    else:
        feeds = []
    form.q.data = question
    return render_template("explore.html", feeds=feeds, form=form)


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
                favicon = get_site_from_link(data.feed.link) + "/favicon.ico"
                new_feed = RssFeed(
                    title=data.feed.title, link=form.rss_link.data, favicon=favicon
                )
                db.session.add(new_feed)
                db.session.commit()
            except:
                db.session.rollback()
            try:
                feed = RssFeed.query.filter_by(link=form.rss_link.data).first()
                current_user.feeds.append(feed)
                db.session.commit()
                flash("Congratutlations, you are now subscribed to this feed")
            except:
                db.session.rollback()
            try:
                add_new_entries(data, new_feed)
                db.session.commit()
            except:
                db.session.rollback()
        except:
            flash("A problem has occurred while parsing this link")
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
    return redirect(url_for("index"))


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
    return redirect(url_for("index"))


# @app.route("/admin/feeds/")
# @login_required
# def admin_feed_list():
#     if current_user.username not in app.config["ADMINS"]:
#         return render_template("404.html"), 404
#     feeds = RssFeed.query.all()
#     return render_template("admin/feed_list.html", feeds=feeds)
#
#
# @app.route("/admin/feeds/<rss_feed>", methods=["GET", "POST"])
# @login_required
# def admin_feed_detail(rss_feed):
#     if current_user.username not in app.config["ADMINS"]:
#         return render_template("404.html"), 404
#     feed = RssFeed.query.filter_by(id=rss_feed).first_or_404()
#     form = AdminModifyFeedForm()
#     if form.validate_on_submit():
#         try:
#             if form.eliminate.data:
#                 db.session.delete(feed)
#                 db.session.commit()
#                 return redirect(url_for("admin_feed_list"))
#             else:
#                 feed.title = form.title.data
#                 feed.link = form.link.data
#             db.session.commit()
#         except:
#             db.session.rollback()
#     form.title.data = feed.title
#     form.link.data = feed.link
#     feeds = feed.posts
#     return render_template("admin/feed_detail.html", form=form, feeds=feeds)
#
#
# @app.route("/admin/entries/")
# @login_required
# def admin_entry_list():
#     if current_user.username not in app.config["ADMINS"]:
#         return render_template("404.html"), 404
#     feeds = RssEntry.query.all()
#     return render_template("admin/entry_list.html", feeds=feeds)
#
#
# @app.route("/admin/entries/<rss_entry>", methods=["GET", "POST"])
# @login_required
# def admin_entry_detail(rss_entry):
#     if current_user.username not in app.config["ADMINS"]:
#         return render_template("404.html"), 404
#     feed = RssEntry.query.filter_by(id=rss_entry).first_or_404()
#     return render_template("admin/entry_detail.html", feed=feed)


# if feeds != []:
#     feeds = feeds.paginate(page, 25, False)
#     next_url = url_for("index", page=feeds.next_num) if feeds.has_next else None
#     prev_url = url_for("index", page=feeds.prev_num) if feeds.has_prev else None
