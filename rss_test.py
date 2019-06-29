import requests
import feedparser
from html.parser import HTMLParser
from rss_reader import db
from rss_reader.models import RssFeed, RssEntry
from dateutil import parser
from dateutil.tz import tzlocal
from lxml.html.clean import clean_html

from requests_futures.sessions import FuturesSession

session = FuturesSession(max_workers=8)


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


def parse(site, parser):
    rss_file = find_link(site, parser)
    return parse_file(rss_file)


def parse_file(link):
    data = requests.get(link).text  # get rss file location
    return feedparser.parse(data)  # parse and return rss file


def find_link(site, parser):
    raw = requests.get(site).text  # get site
    parser.feed(raw)  # parse site
    feed_location = parser.feedLocation  # get rss file location
    return feed_location


links = ["https://realpython.com", "https://www.nytimes.com/"]


def find_links():
    parser = MyHtmlParser()
    removable_links = []
    for link in links:
        rss_link = find_link(link, parser)
        if rss_link:
            try:
                data = parse_file(rss_link)
                removable_links.append(rss_link)
                """


                """
                rss_link_db = RssFeed(title=data.feed.title, link=rss_link)
                db.session.add(rss_link_db)
                db.session.commit()
                """


                """
            except:
                db.session.rollback()
    return list(filter(lambda x: x not in removable_links, links))


def parse_feeds():
    for feed in RssFeed.query.all():
        link = feed.link
        data = parse_file(link)
        add_new_entries(data, feed)


def add_new_entries(data, feed):
    for entry in data.entries:
        # https://stackoverflow.com/questions/51206500/how-to-convert-a-string-datetime-with-unknown-timezone-to-timestamp-in-python
        # timezone_info = {"EDT": "UTC -4", "EST": "UTC -5"}
        time = parser.parse(entry.updated)  # tzinfos=timezone_info)
        # print(time, entry.updated)
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


# links = find_links()
# parse_feeds()

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
