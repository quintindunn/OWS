from crawler import Crawler

import logging
import sys

if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    crawler = Crawler(seed_url="https://wikipedia.org/wiki/webcrawler")  # I like irony.
    while True:
        crawler.step()
