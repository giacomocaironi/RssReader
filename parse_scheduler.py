from rss_reader.parser import parse_feeds


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    while True:
        try:
            parse_feeds()
        except:
            pass
