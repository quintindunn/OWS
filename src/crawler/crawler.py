import sys
import time
import logging
import typing
import functools

import requests.exceptions

sys.path.insert(0, "..")

if typing.TYPE_CHECKING:
    # Allow IDE to find correct import.
    from ..database import db, page_checker

try:
    from .crawlerstats import CrawlerStats
    from .exceptions import NoUrlException
    from .requester import Requester
    from .crawleroptions import BaseCrawlerOptions, DefaultCrawlerOptions
    from .page import Page
    from .robots import does_page_follow_robots_rules
    from .url_checker import check_url_compliance
except ImportError as e:
    from crawlerstats import CrawlerStats
    from exceptions import NoUrlException
    from requester import Requester
    from crawleroptions import BaseCrawlerOptions, DefaultCrawlerOptions
    from page import Page
    from robots import does_page_follow_robots_rules
    from url_checker import check_url_compliance
finally:
    from database import db, page_checker
    page_follows_db_rules = page_checker.page_follows_db_rules

DB_MAX_CONTENT_CHARS = 15000000

logger = logging.getLogger("Crawler")


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
        :param crawler_options: The configuration of the Crawler.
        """

        self.options: BaseCrawlerOptions = crawler_options or DefaultCrawlerOptions()

        self.stats = CrawlerStats()
        self.requester = Requester(crawler_options=self.options)

        self.seed_url: str | None = seed_url or None
        self.enqueued: set[str] = crawled or set()  # For all URLs that have been crawled or are already queued to crawl
        self.to_crawl: list[str] = list(to_crawl or [seed_url])

        self.current_url: str | None = None

        self.db_session = db.Session()

        self.url_compliance_checker = functools.partial(check_url_compliance, self.options)

    def _get_next_url(self) -> str:
        """
        Gets the next URL to crawl and updates Crawler.enqueued.
        :return: Next URL to crawl.
        """
        # Check that we haven't crawled everything.
        logger.debug(f"[URLs] {len(self.to_crawl)} URLs left to crawl.")
        if len(self.to_crawl) == 0:
            raise NoUrlException()

        current_url = self.to_crawl.pop()

        if current_url is None:
            raise NoUrlException()

        self.enqueued.add(current_url)
        return current_url

    def _get_url_robots(self, url: str) -> str:
        # TODO: Implement getting robots.txt file for a URLs domain.
        return ""

    def get_page(self, url: str) -> Page | None:
        """
        Gets a page from the server.
        :param url: URL to the webpage.
        :return: Page or None if there was an error.
        """
        # Perform any checks.
        if self.options.follow_robots_txt and not does_page_follow_robots_rules(url, self._get_url_robots(url)):
            logger.info(f"[Robots.txt] Page @ \"{url[:60]}{'...' if len(url) > 60 else ''}\" conflicts with robots.txt")
            return None

        # Get the page.
        request = self.requester.get(url=url)

        # Do some basic parsing.
        page = Page(
            status_code=request.status_code,
            elapsed=request.elapsed,
            content=request.content,
            response_headers=request.headers,
            url=url
        )

        return page

    def step(self) -> Page | None:
        """
        Steps through an iteration of the crawler.
        """

        start_time = time.time_ns()

        url = self._get_next_url()

        # Get the page, and update the crawling queue to hold the new links.
        logger.info(f"[Crawling] Crawling page \"{url[:60]}{'...' if len(url) > 60 else ''}\"")
        try:
            page = self.get_page(url)

        except requests.exceptions.ConnectionError as e:
            logger.info(f"[Request Error] on page \"{url[:60]}{'...' if len(url) > 60 else ''}\" {e}")
            self.stats.pages_crawled += 1
            self.stats.pages_failed += 1
            return None

        except Exception as e:
            logger.error(f"[GET PAGE ERROR] {e}")
            return None

        if page is None:
            return None

        if 300 > page.status_code >= 200:
            passed_urls = set()

            for url in page.get_links():
                if self.url_compliance_checker(url):
                    passed_urls.add(url)

            self.to_crawl.extend(passed_urls - self.enqueued)
        else:
            logger.info(f"[Response] HTTP {page.status_code} @ \"{url[:60]}{'...' if len(url) > 60 else ''}\"")

        # Update statistics.
        total_time = time.time_ns() - start_time
        self.stats.update(page=page, elapsed_time=total_time)

        # Write new page to database:

        if page_follows_db_rules(page):
            logger.info("[DB] Writing page to database")
            page_model = db.PageModel(
                status_code=page.status_code,
                elapsed=page.elapsed.total_seconds(),
                url=page.url,
                domain=page.domain,
                title=page.html_title,
                content=page.content.decode().encode("UTF-8")[:DB_MAX_CONTENT_CHARS]
            )
            self.db_session.add(page_model)
            self.db_session.commit()
        else:
            logger.info(f"[DB] \"{url[:60]}{'...' if len(url) > 60 else ''}\" doesn't follow database rules.")
        return page
