class NoUrlException(Exception):
    def __init__(self, msg: str = ""):
        super().__init__()
        self.msg = msg

    def __str__(self):
        return self.msg or "No URLs left to crawl!"

    __repr__ = __str__


class WaitBeforeRetryException(Exception):
    def __init__(self, msg: str = ""):
        super().__init__()
        self.msg = msg

    def __str__(self):
        return self.msg or "Cannot crawl page, try again later."
