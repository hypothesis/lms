from contextlib import contextmanager
from urllib.parse import urlencode, urlunparse

from requests import Session


class JSONHTTPClient:
    def __init__(self, host, scheme="https", url_stub=None):
        self.host = host
        self.scheme = scheme
        self.url_stub = url_stub
        self._session = None

    @contextmanager
    def session(self):
        with Session() as session:
            self._session = session
            yield session

    def get_url(self, path, query=None):
        if self.url_stub:
            path = self.url_stub + "/" + path.lstrip("/")

        query = urlencode(query) if query else None

        return urlunparse([self.scheme, self.host, path, None, query, None])

    def call(self, method, path, query=None, headers=None, raw=False, **options):
        response = self._session.request(
            method, url=self.get_url(path, query), headers=headers or {}, **options
        )

        if response.ok:
            if raw:
                return response

            return response.json()

        print(response, response.text)

        # TODO! - Maybe a nice error catch here?
        response.raise_for_status()
