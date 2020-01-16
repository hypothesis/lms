from urllib.parse import urlencode, urlunparse

from requests import request


class JSONHTTPClient:
    def __init__(self, host, scheme="https", url_stub=None):
        self.host = host
        self.scheme = scheme
        self.url_stub = url_stub

    def get_url(self, path, query=None):
        if self.url_stub:
            path = self.url_stub + "/" + path.lstrip("/")

        query = urlencode(query) if query else None

        return urlunparse([self.scheme, self.host, path, None, query, None])

    def call(self, method, path, query=None, headers=None):
        response = request(method, url=self.get_url(path, query), headers=headers or {})

        if response.ok:
            return response.json()

        # TODO! - Maybe a nice error catch here?
        response.raise_for_status()
