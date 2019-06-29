from requests_futures.sessions import FuturesSession
import requests
import feedparser
from dateutil import parser
from lxml.html.clean import clean_html
from rss_reader.models import RssEntry, RssFeed
from rss_reader import app, db


def parse_file(link):
    data = requests.get(link).text  # get rss file location
    return feedparser.parse(data)  # parse and return rss file


def parse_feeds():
    session = FuturesSession(max_workers=256)
    feeds = RssFeed.query.all()
    urls = []
    for feed in feeds:
        urls.append(feed.link)
    responses = []
    for url in urls:
        responses.append(session.get(url))
    for i in range(len(urls)):
        try:
            feed = feeds[i]
            data = responses[i].result()
            add_new_entries(feedparser.parse(data.text), feed)
        except Exception as e:
            print(e)


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
