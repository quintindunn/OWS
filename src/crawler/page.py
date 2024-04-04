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
    def base_url(self):
        protocol, url = self.url.split("//", 1)
        return f"{protocol}//{url.split('/', 1)[0]}"

    @property
    @lru_cache()
    def url_path(self):
        return self.url.split(self.base_url)[1].split("?", 1)[0]

    @property
    @lru_cache()
    def protocol(self):
        return self.base_url.split(":", 1)[0]

    @property
    @lru_cache()
    def domain(self):
        return self.base_url.split("//")[1]

    @property
    @lru_cache()
    def html_title(self) -> str:
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
    def html_tree(self):
        return document_fromstring(self.content)

    def get_links(self) -> set[str]:
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
