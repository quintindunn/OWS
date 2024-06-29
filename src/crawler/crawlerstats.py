try:
    from .page import Page
except ImportError:
    from page import Page


class CrawlerStats:
    def __init__(self):
        self.pages_crawled: int = 0
        self.pages_failed: int = 0
        self.pages_ok: int = 0

        self.total_crawl_time: int = 0

    @property
    def average_crawl_time(self) -> float:
        """
        Gets the average time for the crawler to crawl a page.
        :return: A float of the average time to crawl a page.
        """
        return self.total_crawl_time / self.pages_crawled

    def update(self, page: Page, elapsed_time: int) -> None:
        """
        Updates the CrawlerStats object with the new time for the page.
        :param page: Page object containing relevant information about that crawler step.
        :param elapsed_time: Time for the crawler to process the page.
        :return: None
        """
        self.pages_crawled += 1
        okay = page.status_code < 300

        if okay:
            self.pages_ok += 1
        else:
            self.pages_failed += 1

        self.total_crawl_time += elapsed_time
