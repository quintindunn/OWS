import os.path
import shutil
from unittest import TestCase

import sys

sys.path.append("..")

from crawler.urls import get_protocol_and_domain_from_url


class TestURLs(TestCase):
    def test_protocol_domain(self):
        urls = {
            "http://example.com/path?query=123#section": ["http:", "example.com"],
            "https://example.com?query": ["https:", "example.com"],
            "http://example.com/path": ["http:", "example.com"],
            "http://example.com": ["http:", "example.com"],
            "https://example.com/path?query#section": ["https:", "example.com"],
            "http://example.com/path/another#section": ["http:", "example.com"],
            "http://example.com/path/another?query": ["http:", "example.com"],
            "http://example.com?query#section": ["http:", "example.com"],
            "http://subdomain.example.com/path": ["http:", "subdomain.example.com"],
            "https://example.com:8080/path": ["https:", "example.com:8080"],
            "http://example.com//////path": ["http:", "example.com"],
            "http://example.com/path?query=1/2/3": ["http:", "example.com"],
            "http://example.com/path#": ["http:", "example.com"],
            "http://example.com?query?more": ["http:", "example.com"],
            "http://example.com/path;param?query#fragment": ["http:", "example.com"],
            "https://example.com#fragment": ["https:", "example.com"],
            "http://192.168.0.1/path": ["http:", "192.168.0.1"],
            "http://[::1]/path": ["http:", "[::1]"],
        }

        for url, expected in urls.items():
            protocol, domain = get_protocol_and_domain_from_url(url)
            self.assertEqual([protocol, domain], expected)
