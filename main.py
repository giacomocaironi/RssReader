from rss_reader import app, db
from rss_reader.models import User, RssFeed, RssEntry


@app.shell_context_processor
def make_shell_context():
    return {"db": db, "User": User, "RssFeed": RssFeed, "RssEntry": RssEntry}


app.run(host="0.0.0.0")
