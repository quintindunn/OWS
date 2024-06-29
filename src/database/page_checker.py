import sys
import typing

sys.path.insert(0, "..")

if typing.TYPE_CHECKING:
    # Allow IDE to find correct import.
    from ..crawler.page import Page
    from ..crawler.crawleroptions import BaseCrawlerOptions

from crawler.page import Page
from crawler.crawleroptions import BaseCrawlerOptions


def page_follows_db_rules(crawler_options: BaseCrawlerOptions, page: Page):
    # Check content-type
    # TODO: Improve content-type check as this will disregard many good pages.
    headers = page.headers

    if crawler_options.check_content_type:
        content_type = headers.get("content-type")
        for accepted_content_type in crawler_options.accepted_content_types:
            if content_type and accepted_content_type in content_type:
                break
        else:
            return False

    return True
