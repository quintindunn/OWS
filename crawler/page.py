from datetime import timedelta


class Page:
    def __init__(self, status_code: int, elapsed: timedelta, content: bytes):
        self.status_code: int = status_code
        self.elapsed = elapsed

        self.content: bytes = content
