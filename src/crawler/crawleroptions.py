class BaseCrawlerOptions:
    def __init__(self):
        # Should the crawler follow the rules of /robots.txt (https://www.rfc-editor.org/rfc/rfc9309.html)
        self.follow_robots_txt: bool = True

        # What should the user agent (UA) for the crawler be
        self.ua: str | None = None


class DefaultCrawlerOptions(BaseCrawlerOptions):
    def __init__(self):
        super().__init__()
        self.follow_robots_txt: bool = True
        self.ua: str = "OWS-CRAWLER/0.1-DEV (https://github.com/quintindunn/OWS)"
