try:
    from .crawleroptions import BaseCrawlerOptions
except ImportError:
    from crawleroptions import BaseCrawlerOptions

import requests


class Requester:
    def __init__(self, crawler_options: BaseCrawlerOptions):
        self.options: BaseCrawlerOptions = crawler_options
        self.base_headers = {
            "User-Agent": crawler_options.ua
        }

    def get(self, url: str, *args, headers: dict | None = None, is_robots: bool = False,
            **kwargs) -> requests.Response:
        """
        Makes a GET request to the given URL but passes the base headers into the request.
        :param url: URL to make the request to.
        :param args: args for requests.get(*args)
        :param headers: Headers to append to the base headers.
        :param is_robots: Is the request to a robots.txt file.
        :param kwargs: kwargs for requests.get(*args, **kwargs)
        :return: requests.Response object.
        """
        # Build the headers used in the request.
        local_headers = self.base_headers.copy()
        headers = headers or dict()
        local_headers.update(headers)
        if is_robots:
            request = requests.get(url, headers=headers, timeout=self.options.robots_timeout, *args, **kwargs)
        else:
            request = requests.get(url, headers=headers, *args, **kwargs)
        return request
