from rss_reader import app, db
from rss_reader.models import User, RssFeed, RssEntry
import flask_whooshalchemy as wa


@app.shell_context_processor
def make_shell_context():
    return {"db": db, "User": User, "RssFeed": RssFeed, "RssEntry": RssEntry}


wa.whoosh_index(app, RssFeed)
if __name__ == "__main__":
    app.run(host="0.0.0.0")
