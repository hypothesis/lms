class RetriableHTTPException(Exception):
    def __init__(self, message, kwargs):
        self.message = message
        self.kwargs = kwargs


class BadBearerToken(RetriableHTTPException):
    pass
