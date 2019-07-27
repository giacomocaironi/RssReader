from requests_futures.sessions import FuturesSession
import requests
import feedparser
from dateutil import parser
from lxml.html.clean import clean_html
from rss_reader.models import RssEntry, RssFeed
from rss_reader import app, db
from html.parser import HTMLParser
from datetime import datetime, timedelta
import logging
import time


class MyHtmlParser(HTMLParser):
    feedLocation = None

    def handle_starttag(self, tag, attrs):
        if tag != "link":
            return
        type = None
        href = None
        for attr in attrs:
            if attr[0] == "type":
                type = attr[1]
            if attr[0] == "href":
                href = attr[1]
        if type:
            if "xml" in type:
                self.feedLocation = href


def find_rss_link(site, parser):
    raw = requests.get(site).text  # get site
    parser.feed(raw)  # parse site
    feed_location = parser.feedLocation  # get rss file location
    if not feed_location:
        return None
    if feed_location[:4] != "http":
        file = feed_location
        base_site = site.split("/")[2]
        feed_location = "http://" + base_site + file
    return feed_location


def parse_file(link):
    data = requests.get(link).text  # get rss file location
    return feedparser.parse(data)  # parse and return rss file


def parse_link(link):
    session = FuturesSession(max_workers=32)
    urls = [find_rss_link(link, MyHtmlParser())]
    urls.append(link)
    responses = []
    for url in urls:
        responses.append(session.get(url))
    for response in responses:
        try:
            data = response.result().text
            data = feedparser.parse(data)
            href = data.feed.links[0].href
            return data
        except:
            pass
    return None  # parse and return rss file


def parse_feeds():
    session = FuturesSession(max_workers=256)
    feeds = RssFeed.query.all()
    urls = []
    for feed in feeds:
        urls.append(feed.link)
    responses = []
    delete_entries()
    for url in urls:
        responses.append(session.get(url))
    for i in range(len(urls)):
        try:
            feed = feeds[i]
            data = responses[i].result()
            add_new_entries(feedparser.parse(data.text), feed)
            # logging.info(str(time.time()) + " " + str(i))
        except Exception as e:
            print(e)
            logging.info(e)
    # delete_entries() uncomment this and comment the previous to delete every
    # entry not in the date, also the ones in the feed file
    logging.info("feeds parsed")
    logging.info(datetime.now())


def add_new_entries(data, feed):
    for entry in data.entries:
        time = parser.parse(entry.updated)
        try:
            if (
                RssEntry.query.filter_by(href=entry.link, feed_id=feed.id).count() > 0
            ):  # do not add doubles
                continue
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


# assolutamente da migliorare
def delete_entries():
    date = datetime.utcnow() + timedelta(days=-7)
    for entry in RssEntry.query.filter(RssEntry.date < date):
        db.session.delete(entry)
    for entry in RssEntry.query.filter_by(feed_file=None):
        db.session.delete(entry)
    db.session.commit()
