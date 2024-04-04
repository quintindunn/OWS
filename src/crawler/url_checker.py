try:
    from .crawleroptions import BaseCrawlerOptions
except ImportError as e:
    from crawleroptions import BaseCrawlerOptions


def check_url_compliance(crawler_options: BaseCrawlerOptions, url: str) -> bool:
    """
    Checks if the URL given complies with all rules.
    :param crawler_options: Options for the crawler.
    :param url: URL to check.
    :return: True if the URL complies with rules, otherwise False.
    """
    # Check file ending
    segments = url.replace("//", "/").split("/")

    # Check to see if these checks even apply:
    if len(segments) == 2 or "." not in segments[-1]:
        return True

    ending_segment = segments[-1]
    path_ending = ending_segment.split(".")[-1]

    if path_ending in crawler_options.ignored_url_endings:
        return False

    return True
