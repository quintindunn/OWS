class BaseCrawlerOptions:
    def __init__(self):
        self.follow_robots_txt: bool
        self.user_agent: str


class DefaultCrawlerOptions(BaseCrawlerOptions):
    def __init__(self):
        super().__init__()
        self.follow_robots_txt: bool = True
        self.user_agent: str = "OWS-CRAWLER/0.1-DEV (https://github.com/quintindunn/OWS)"
