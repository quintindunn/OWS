from datetime import timedelta

from lxml.html import document_fromstring


class Page:
    def __init__(self, status_code: int, elapsed: timedelta, content: bytes, url: str):
        self.status_code: int = status_code
        self.elapsed = elapsed
        self.url = url

        self.content: bytes = content

    @property
    def base_url(self):
        protocol, url = self.url.split("//", 1)
        return f"{protocol}//{url.split('/', 1)[0]}"

    @property
    def url_path(self):
        return self.url.split(self.base_url)[1].split("?", 1)[0]

    @property
    def protocol(self):
        return self.base_url.split(":", 1)[0]

    def get_links(self) -> set[str]:
        results = set()

        tree = document_fromstring(self.content)
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
