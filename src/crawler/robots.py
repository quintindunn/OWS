import datetime
import typing
import sys

from urllib import robotparser

sys.path.insert(0, "..")

if typing.TYPE_CHECKING:
    # Allow IDE to find correct import.
    from ..database import db

try:
    from .crawleroptions import BaseCrawlerOptions, DefaultCrawlerOptions
    from .exceptions import WaitBeforeRetryException
except ImportError as e:
    from crawleroptions import BaseCrawlerOptions, DefaultCrawlerOptions
    from exceptions import WaitBeforeRetryException


def does_page_follow_robots_rules(
    crawler_options: BaseCrawlerOptions, url: str, robots: str, domain: "db.DomainModel"
) -> bool:
    parser = robotparser.RobotFileParser()
    parser.parse(robots.splitlines())

    if not parser.can_fetch(useragent=crawler_options.ua, url=url):
        return False

    try:
        crawl_delay = parser.crawl_delay(crawler_options.ua)
        request_delay = parser.request_rate(crawler_options.ua)

        now = datetime.datetime.now()
        if crawl_delay and (now - domain.last_crawled).total_seconds() < int(
            crawl_delay
        ):
            raise WaitBeforeRetryException()

        if request_delay and (now - domain.last_crawled).total_seconds() < int(
            request_delay.seconds
        ):
            raise WaitBeforeRetryException()
    except ValueError:
        pass

    # TODO: add more checks for things such as if the page is crawled too often.
    return True
