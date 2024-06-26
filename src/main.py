import json
import os.path
import random
import shutil

from crawler import Crawler

import logging
import sys

if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    with open("./seeds.txt", "r") as f:
        seeds = [i.strip() for i in f.readlines()]

    seed_url = random.choice(seeds)

    if os.path.isfile("./to_crawl.json"):
        with open("./to_crawl.json", "r") as f:
            to_crawl = json.load(f)
            crawler = Crawler(seed_url=seed_url, to_crawl=to_crawl)
    else:
        crawler = Crawler(seed_url=seed_url)
    try:
        while True:
            crawler.step()
    except KeyboardInterrupt as e:
        pass

    to_crawl = crawler.url_manager.to_crawl

    if os.path.isfile("./to_crawl.json"):
        shutil.move("./to_crawl.json", "./to_crawl.json.old")
    with open("./to_crawl.json", "w") as f:
        json.dump(to_crawl, f)
