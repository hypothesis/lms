from unittest.mock import sentinel

from lms.services.digest import DigestService, service_factory


class TestDigestService:
    def test_it(self):
        DigestService()


class TestServiceFactory:
    def test_it(self):
        service_factory(sentinel.context, sentinel.request)
