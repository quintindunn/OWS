import requests


class Crawler:
    def __init__(self, seed_url: str,
                 crawled: set[str] | None = None,
                 to_crawl: set[str] | None = None

                 ):
        self.seed_url: str
        self.crawled: set[str]
        self.to_crawl: set[str]

