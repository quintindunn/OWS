import time

from crawler import Crawler
from crawler.urls import URLManager

from threading import Thread

import json
import os.path
import random
import shutil
import logging
import sys


def run_instance(url_man: URLManager):
    crawler = Crawler(url_manager=url_man)
    instances.append(crawler)
    while LIVE:
        crawler.step()


def launch_instance(url_man: URLManager):
    thread = Thread(target=run_instance, kwargs={"url_man": url_man}, daemon=True)
    thread.start()


def dump_to_crawl(url_man: URLManager):
    _to_crawl = url_man.to_crawl.copy()

    if os.path.isfile("./to_crawl.json"):
        shutil.move("./to_crawl.json", "./to_crawl.json.old")
    with open("./to_crawl.json", "w") as f:
        json.dump(_to_crawl, f)


def load_data():
    with open("./seeds.txt", "r") as f:
        seeds = [i.strip() for i in f.readlines()]

    if os.path.isfile("./to_crawl.json"):
        with open("./to_crawl.json", "r") as f:
            to_crawl = json.load(f)
    else:
        to_crawl = None

    return seeds, to_crawl


LIVE = True
INSTANCE_COUNT = int(sys.argv[1]) if len(sys.argv) == 2 else 2
instances = []


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    logger = logging.getLogger("[Main]")

    seeds, to_crawl = load_data()
    seed_url = random.choice(seeds)

    url_manager = URLManager(seed_url=seed_url, crawled=None, to_crawl=to_crawl)

    # If instance count > 1 multithreading will be used.
    if INSTANCE_COUNT > 1:
        for instance in range(1, INSTANCE_COUNT + 1):
            logger.info(f"Starting crawler instance #{instance}")
            launch_instance(url_man=url_manager)

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            dump_to_crawl(url_man=url_manager)

    else:
        try:
            run_instance(url_man=url_manager)
        except KeyboardInterrupt:
            dump_to_crawl(url_man=url_manager)
