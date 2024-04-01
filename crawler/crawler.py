from datetime import timedelta

import time

import requests.exceptions

try:
    from .crawlerstats import CrawlerStats
    from .exceptions import NoUrlException
    from .requester import Requester
    from .crawleroptions import BaseCrawlerOptions, DefaultCrawlerOptions
    from .page import Page
except ImportError:
    from crawlerstats import CrawlerStats
    from exceptions import NoUrlException
    from requester import Requester
    from crawleroptions import BaseCrawlerOptions, DefaultCrawlerOptions
    from page import Page


class Crawler:
    def __init__(self, seed_url: str,
                 crawled: set[str] | None = None,
                 to_crawl: set[str] | None = None,
                 crawler_options: BaseCrawlerOptions | None = None
                 ):
        """
        :param seed_url: The URL to seed from.
        :param crawled: A set of pages to ignore as they've been crawled already.
        :param to_crawl: A set of pages to crawl, these shouldn't intersect with crawled.
        """

        self.options: BaseCrawlerOptions = crawler_options or DefaultCrawlerOptions()

        self.stats = CrawlerStats()
        self.requester = Requester(crawler_options=self.options)

        self.seed_url: str | None = seed_url or None
        self.enqueued: set[str] = crawled or set()  # For all URLs that have been crawled or are already queued to crawl
        self.to_crawl: list[str] = list(to_crawl or [seed_url])

        self.current_url: str | None = None

    def _get_next_url(self) -> str:
        # Check that we haven't crawled everything.
        if len(self.to_crawl) == 0:
            raise NoUrlException

        current_url = self.to_crawl.pop()

        if current_url is None:
            raise NoUrlException()

        self.enqueued.add(current_url)
        return current_url

    def get_page(self, url: str) -> Page:
        # Perform any checks.
        if self.options.follow_robots_txt:
            # TODO: Implement robots.txt check.
            ...

        # Get the page.
        request = self.requester.get(url=url)

        # Do some basic parsing.
        page = Page(
            status_code=request.status_code,
            elapsed=request.elapsed,
            content=request.content,
            url=url
        )

        return page

    def step(self):
        start_time = time.time_ns()

        url = self._get_next_url()

        # Get the page, and update the crawling queue to hold the new links.
        try:
            page = self.get_page(url)
        except requests.exceptions.ConnectionError:
            self.stats.pages_crawled += 1
            self.stats.pages_failed += 1
            return

        if 300 > page.status_code >= 200:
            self.to_crawl.extend(page.get_links() - self.enqueued)
        else:
            print(page.status_code)

        # Update statistics.
        total_time = time.time_ns() - start_time
        self.stats.update(page=page, elapsed_time=total_time)

        return page


if __name__ == '__main__':
    crawler = Crawler(seed_url="https://wikipedia.org/wiki/webcrawler")  # I like irony.

    while True:
        crawler.step()
