import datetime

from sqlalchemy import func

import sys
import time
import logging
import typing
import functools

import requests.exceptions

sys.path.insert(0, "..")

from .crawlerstats import CrawlerStats  # noqa
from .exceptions import NoUrlException, WaitBeforeRetryException  # noqa
from .requester import Requester  # noqa
from .crawleroptions import BaseCrawlerOptions, DefaultCrawlerOptions  # noqa
from .page import Page  # noqa
from .robots import does_page_follow_robots_rules  # noqa
from .url_checker import check_url_compliance  # noqa
from .urls import URLManager, get_protocol_and_domain_from_url  # noqa

from database import db, page_checker  # noqa (Ignore import error)

if typing.TYPE_CHECKING:
    # Allow IDE to find correct import.
    from ..database import db, page_checker

DB_MAX_CONTENT_CHARS = 15000000

logger = logging.getLogger("Crawler")


class Crawler:
    def __init__(
        self,
        url_manager: URLManager,
        crawler_options: BaseCrawlerOptions | None = None,
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

        self.url_manager = url_manager

        self.current_url: str | None = None

        self.db_session = db.Session()

        self.url_compliance_checker = functools.partial(
            check_url_compliance, self.options
        )
        self.page_follows_db_rules = functools.partial(
            page_checker.page_follows_db_rules, self.options
        )

    def get_domain_robots(self, domain: str, protocol: str) -> str:
        protocol = protocol + (":" if not protocol[-1] == ":" else "")
        robots_txt_url = f"{protocol}//{domain}/robots.txt"
        logger.info(f'[Robots] Getting "{domain}"\'s robots.txt.')
        robots_txt_request = self.requester.get(robots_txt_url, is_robots=True)

        if robots_txt_request.status_code == 404:
            return ""

        return robots_txt_request.text

    @functools.lru_cache(maxsize=1024)
    def get_domain(self, domain: str) -> db.DomainModel:
        domain_model = (
            self.db_session.query(db.DomainModel)
            .filter(func.lower(db.DomainModel.domain) == domain)
            .first()
        )
        return domain_model

    @functools.lru_cache(maxsize=1024)
    def get_robots_txt(self, domain):
        domain_model = (
            self.db_session.query(db.DomainModel)
            .filter(func.lower(db.DomainModel.domain) == domain)
            .first()
        )

        if not domain_model:
            try:
                domain_model = db.DomainModel(
                    domain=domain, robots=self.get_domain_robots(domain, "http")
                )
                self.db_session.add(domain_model)
                self.db_session.commit()
            except requests.exceptions.ConnectionError:
                return ""

        return domain_model.robots

    def get_page(self, url: str) -> Page | None:
        """
        Gets a page from the server.
        :param url: URL to the webpage.
        :return: Page or None if there was an error.
        """
        # Perform any checks.

        protocol, domain = get_protocol_and_domain_from_url(url)

        domain_model = self.get_domain(domain)

        logger_url_str = f"\"{url[:60]}{'...' if len(url) > 60 else ''}\""

        try:
            if self.options.follow_robots_txt and not does_page_follow_robots_rules(
                self.options, url, self.get_robots_txt(domain), domain=domain_model
            ):
                logger.info(
                    f"[Robots.txt] Page @ {logger_url_str} conflicts with robots.txt"
                )
                return None
        except WaitBeforeRetryException:
            self.url_manager.add_to_to_crawl_queue(url, domain)
            logger.info(
                f"[Robots.txt] Cannot crawl {logger_url_str} as it was crawled too recently."
            )

        # Get the page.
        request = self.requester.get(
            url=url, stream=True, timeout=self.options.page_timeout
        )

        content = b""

        max_bytes = self.options.max_page_size
        chunk_size = self.options.content_buffer_size
        total_bytes = 0

        for chunk in request.iter_content(chunk_size=chunk_size):
            total_bytes += len(chunk)
            content += chunk
            if total_bytes >= max_bytes:
                break

        if content == b"":
            return None

        # Do some basic parsing.
        page = Page(
            status_code=request.status_code,
            elapsed=request.elapsed,
            content=content,
            response_headers=request.headers,
            url=url,
        )

        if domain_model:
            domain_model.last_crawled = datetime.datetime.now()
            self.db_session.commit()

        return page

    def step(self) -> Page | None:
        """
        Steps through an iteration of the crawler.
        """
        try:
            start_time = time.time_ns()

            url = self.url_manager.get_next_url()

            # Check if domain is in domain table.
            protocol, domain = get_protocol_and_domain_from_url(url)

            domain_model = (
                self.db_session.query(db.DomainModel)
                .filter(func.lower(db.DomainModel.domain) == domain)
                .all()
            )

            if not domain_model:
                try:
                    domain_model = db.DomainModel(
                        domain=domain, robots=self.get_domain_robots(domain, protocol)
                    )
                    self.db_session.add(domain_model)
                    self.db_session.commit()
                except requests.exceptions.ConnectionError:
                    pass

            # Get the page, and update the crawling queue to hold the new links.
            logger.info(
                f"[Crawling] Crawling page \"{url[:60]}{'...' if len(url) > 60 else ''}\""
            )
            try:
                page = self.get_page(url)

            except requests.exceptions.ConnectionError as e:
                logger.info(
                    f"[Request Error] on page \"{url[:60]}{'...' if len(url) > 60 else ''}\" {e}"
                )
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

                self.url_manager.add_many_to_to_crawl_queue(passed_urls)

            else:
                logger.info(
                    f"[Response] HTTP {page.status_code} @ \"{url[:60]}{'...' if len(url) > 60 else ''}\""
                )

            # Update statistics.
            total_time = time.time_ns() - start_time
            self.stats.update(page=page, elapsed_time=total_time)

            # Write new page to database:

            if self.page_follows_db_rules(page):
                logger.info("[DB] Writing page to database")
                page_model = db.PageModel(
                    status_code=page.status_code,
                    elapsed=page.elapsed.total_seconds(),
                    url=page.url,
                    domain=page.domain,
                    title=page.html_title,
                    content=page.content.decode().encode("UTF-8")[
                        :DB_MAX_CONTENT_CHARS
                    ],
                )
                self.db_session.add(page_model)

                # Save to db.
                self.db_session.commit()
            else:
                logger.info(
                    f"[DB] \"{url[:60]}{'...' if len(url) > 60 else ''}\" doesn't follow database rules."
                )
            return page
        except NoUrlException as e:
            raise e
        except Exception as e:
            logger.error(f"[STEP ERROR] Error in step {e}")
