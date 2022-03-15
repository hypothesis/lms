from unittest.mock import sentinel

import pytest

from lms.services.aes import AESService, factory


class TestAESService:
    @pytest.mark.parametrize("text, expected", [(b"TEXT", b"TEXT"), ("TEXT", b"TEXT")])
    def test_it(self, svc, text, expected):
        iv = svc.build_iv()
        encrypted = svc.encrypt(iv, text)

        assert svc.decrypt(iv, encrypted) == expected

    @pytest.fixture
    def svc(self, pyramid_request):
        return AESService(pyramid_request.registry.settings["aes_secret"])


class TestFactory:
    def test_it(self, pyramid_request):
        aes_service = factory(sentinel.context, pyramid_request)

        assert isinstance(aes_service, AESService)
