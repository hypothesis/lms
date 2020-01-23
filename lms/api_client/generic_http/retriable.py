from contextlib import contextmanager

from lms.api_client.generic_http.exceptions import RetriableHTTPException


class retriable:
    _retry_handler = None

    def __init__(self, function):
        self.function = function

    # Descriptor get: https://rszalski.github.io/magicmethods/#descriptor
    def __get__(self, instance, owner=None):
        def wrapper(*args, **kwargs):
            try:
                # Instance here is 'self' to the called function
                return self.function(instance, *args, **kwargs)

            except RetriableHTTPException as e:
                # If we are in the _retry_handler context manager call the handler
                if self._retry_handler:
                    return self._retry_handler(e)

                # If not just bail
                raise

        return wrapper

    @classmethod
    @contextmanager
    def retry_handler(cls, retry_handler):
        cls._retry_handler = retry_handler
        yield
        cls._retry_handler = None
