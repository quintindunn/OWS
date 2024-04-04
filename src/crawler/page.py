from functools import lru_cache
from datetime import timedelta

from lxml.html import document_fromstring


class Page:
    def __init__(self, status_code: int, elapsed: timedelta, content: bytes, url: str):
        self.status_code: int = status_code
        self.elapsed = elapsed
        self.url = url

        self.content: bytes = content

    @property
    @lru_cache()
    def base_url(self) -> str:
        """
        Gets the base URL for the page.
        i.e.: https://example.com/something/here -> https://example.com
        :return: The base URL for the page.
        """

        protocol, url = self.url.split("//", 1)
        return f"{protocol}//{url.split('/', 1)[0]}"

    @property
    @lru_cache()
    def url_path(self) -> str:
        """
        Returns the path for the URL.
        i.e.: https://example.com/something/here -> /something/here
        :return: The URLs path
        """

        return self.url.split(self.base_url)[1].split("?", 1)[0]

    @property
    @lru_cache()
    def protocol(self) -> str:
        """
        Returns the HTTP protocol for the URL.
        i.e.: https://example.com/something/here -> https
        :return: The HTTP protocol.
        """

        return self.base_url.split(":", 1)[0]

    @property
    @lru_cache()
    def domain(self) -> str:
        """
        Returns the domain for the URL.
        i.e.: https://example.com/something/here -> example.com
        :return: The domain for the URL.
        """

        return self.base_url.split("//")[1]

    @property
    @lru_cache()
    def html_title(self) -> str:
        """
        Gets the page's title from the HTML from either a title tag or meta tag in that order.
        :return: The page's title.
        """

        tree = self.html_tree
        title_element = tree.find(".//title")
        if title_element is not None:
            return title_element.text

        meta_title = tree.xpath("//meta[@name='title']/@content")
        if meta_title:
            return meta_title[0]

        return ""

    @property
    @lru_cache()
    def html_tree(self) -> document_fromstring:
        """
        Gets the LXML html tree.
        :return: LXML html tree.
        """

        return document_fromstring(self.content)

    def get_links(self) -> set[str]:
        """
        Gets all the href links from anchor tags from the HTML of the webpage.
        :return: A set of strings with the URLs.
        """

        tree = self.html_tree
        results = set()

        hrefs = set(filter(lambda args: args[1] == "href", tree.iterlinks()))
        links = set(filter(lambda args: args[0].tag == "a", hrefs))

        base_url = self.base_url
        path = self.url_path
        protocol = self.protocol

        for elem, reference_type, link, position in list(links)[:100]:
            # See if link is absolute using current protocol
            if link.startswith("//"):
                final_link = f"{protocol}:{link}"

            # Check if link is relative to current url.
            elif link.startswith("/"):
                final_link = base_url + link

            elif link.startswith("#"):
                continue
            elif ":" not in link:
                # TODO: Verify this is correct.
                final_link = base_url + path + link

            elif link.split(":")[0] not in ("http", "https"):
                continue
            else:
                final_link = link

            # TODO: add other sanitization

            results.add(final_link)
        return results
