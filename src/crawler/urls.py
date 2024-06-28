try:
    from .exceptions import (
        NoUrlException,
        WaitBeforeRetryException,
        InvalidURLException,
    )
except ImportError as _:
    from exceptions import NoUrlException, WaitBeforeRetryException, InvalidURLException

import random


def get_protocol_and_domain_from_url(url: str):
    logger_url_str = f"\"{url[:60]}{'...' if len(url) > 60 else ''}\""
    if "//" not in url:
        raise InvalidURLException(f"{logger_url_str} is not a supported url.")

    protocol, _url = url.split("//", 1)  # https:, example.com/test

    if "?" in _url and "/" in _url and _url.index("?") < _url.index("/"):
        domain = _url.split("?", 1)[0]
    elif "?" in url and "/" not in url:
        domain = _url.split("?", 1)[0]
    elif "/" in _url:
        domain = _url.split("/", 1)[0]
    else:
        domain = _url
    return protocol, domain


class URLManager:
    def __init__(
        self,
        seed_url: str,
        crawled: set[str] | None = None,
        to_crawl: dict[str, list[str]] | None = None,
    ):
        self.seed_url: str | None = seed_url or None
        self.enqueued: set[str] = (
            crawled or set()
        )  # For all URLs that have been crawled or are already queued to crawl
        self.to_crawl: dict[str, list[str]] = dict()

        self.url_count = 0

        if to_crawl:
            self.to_crawl = to_crawl
        else:
            _, domain = get_protocol_and_domain_from_url(seed_url)
            self.to_crawl[domain] = [seed_url]

    def get_next_url(self) -> str:
        """
        Gets the next URL to crawl and updates Crawler.enqueued.
        :return: Next URL to crawl.
        """
        # Check that we haven't crawled everything.
        if len(self.to_crawl) == 0:
            raise NoUrlException()
        domain_choice = random.choice(list(self.to_crawl.keys()))
        current_url = random.choice(self.to_crawl[domain_choice])

        self.to_crawl[domain_choice].remove(current_url)

        if len(self.to_crawl[domain_choice]) == 0:
            del self.to_crawl[domain_choice]

        if current_url is None:
            raise NoUrlException()

        self.enqueued.add(current_url)

        return current_url

    def add_to_to_crawl_queue(self, url: str, domain: str | None = None):
        if not url.lower().startswith("http://") and not url.lower().startswith(
            "https://"
        ):
            return

        if domain is None:
            _, domain = get_protocol_and_domain_from_url(url)

        if domain in self.to_crawl.keys():
            self.to_crawl[domain].append(url)
        else:
            self.to_crawl[domain] = [url]

    def add_many_to_to_crawl_queue(self, urls: set[str]):
        urls_to_add = urls - self.enqueued

        for url in urls_to_add:
            self.add_to_to_crawl_queue(url)
