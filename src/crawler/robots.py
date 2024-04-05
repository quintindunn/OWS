from urllib import robotparser

try:
    from .crawleroptions import BaseCrawlerOptions, DefaultCrawlerOptions
except ImportError as e:
    from crawleroptions import BaseCrawlerOptions, DefaultCrawlerOptions


def does_page_follow_robots_rules(crawler_options: BaseCrawlerOptions, url: str, robots: str) -> bool:
    parser = robotparser.RobotFileParser()
    parser.parse(robots.splitlines())

    url_allowed = parser.can_fetch(useragent=crawler_options.ua, url=url)
    # TODO: add more checks for things such as if the page is crawled too often.
    return url_allowed
