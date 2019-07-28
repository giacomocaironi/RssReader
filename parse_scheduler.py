from rss_reader.parser import parse_feeds
import logging


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    while True:
        try:
            parse_feeds()
        except KeyboardInterrupt:
            break
        except:
            pass
