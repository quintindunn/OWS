class BaseCrawlerOptions:
    def __init__(self):
        # Should the crawler follow the rules of /robots.txt (https://www.rfc-editor.org/rfc/rfc9309.html)
        self.follow_robots_txt: bool = True

        # How long to wait for request to /robots.txt to complete.
        self.robots_timeout = 10

        # What should the user agent (UA) for the crawler be
        self.ua: str | None = None

        # What URL endings to ignore
        self.check_url_ending: bool = True
        self.ignored_url_endings: set[str] = set()

        # Check the content-type from the response headers
        self.check_content_type: bool = True

        # Max page content size
        self.max_page_size = 1.5e7  # 15 mb.

        # Request stream buffer size.
        self.content_buffer_size = 2048

        # How long to wait before timeing out request to a page (not including robots.txt see: self.robots_timeout)
        self.page_timeout = 20


class DefaultCrawlerOptions(BaseCrawlerOptions):
    def __init__(
        self,
        ignored_file_extensions_path: str = "./configs/ignored_file_extensions.txt",
    ):
        super().__init__()

        self.ua: str = "OWS-CRAWLER/0.1-DEV (https://github.com/quintindunn/OWS)"

        with open(ignored_file_extensions_path, "r") as f:
            extensions = f.readlines()[1:]
        self.ignored_url_endings = set(extensions)
