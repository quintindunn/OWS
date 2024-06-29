import socket
from unittest import TestCase

import sys

sys.path.append("..")

from crawler.networking import is_host_private


class TestURLs(TestCase):
    def test_private_ips(self):
        private = True
        public = False

        cases = [
            ["google.com", public],
            ["8.8.8.8", public],
            ["1.1.1.1", public],
            ["example.com", public],
            ["github.com", public],
            ["localhost", private],
            ["127.0.0.1", private],
            [socket.gethostbyname(socket.gethostname()), private],
        ]

        for host, expected in cases:
            is_private = is_host_private(host=host)
            self.assertEqual(is_private, expected)
