from unittest.mock import sentinel

import pytest
from Cryptodome.Cipher import AES

from lms.services.aes import AESService, factory


class TestAESService:
    @pytest.mark.parametrize("text, expected", [(b"TEXT", b"TEXT"), ("TEXT", b"TEXT")])
    def test_it(self, svc, text, expected):
        iv = svc.build_iv()
        encrypted = svc.encrypt(iv, text)

        assert svc.decrypt(iv, encrypted) == expected

    @pytest.mark.parametrize(
        "iv,encrypted,text",
        [
            (
                b"\xa4\xb22?\x14\x11\xa1\x04\x80\xe5\xa6\x13\xb4\xdd\x7f\xf7",
                b"2j\x1a\xbd",
                b"TEXT",
            ),
            # Same text, different IV
            (
                b"M\xac\x95\xa4!\x93\xd9]\xfbRo\xc3\xe5\xb0\xd5X",
                b".d\x1e]",
                b"TEXT",
            ),
        ],
    )
    def test_decrypt(self, svc, iv, encrypted, text):
        assert svc.decrypt(iv, encrypted) == text

    @pytest.mark.parametrize(
        "iv,text,encrypted",
        [
            (
                b"\xa4\xb22?\x14\x11\xa1\x04\x80\xe5\xa6\x13\xb4\xdd\x7f\xf7",
                b"TEXT",
                b"2j\x1a\xbd",
            ),
            # Same text, different IV
            (
                b"M\xac\x95\xa4!\x93\xd9]\xfbRo\xc3\xe5\xb0\xd5X",
                b"TEXT",
                b".d\x1e]",
            ),
            # Same text, as str
            (
                b"M\xac\x95\xa4!\x93\xd9]\xfbRo\xc3\xe5\xb0\xd5X",
                "TEXT",
                b".d\x1e]",
            ),
        ],
    )
    def test_encrypt(self, svc, iv, encrypted, text):
        assert svc.encrypt(iv, text) == encrypted

    def test_encrypt_aes_settings(self, svc, AES, pyramid_request):
        encrypted = svc.encrypt("IV", "TEXT")

        AES.new.assert_called_once_with(
            pyramid_request.registry.settings["aes_secret"], AES.MODE_CFB, "IV"
        )
        assert encrypted == AES.new.return_value.encrypt.return_value

    def test_build_iv(self, svc):
        iv = svc.build_iv()

        assert isinstance(iv, bytes)
        assert len(iv) == AES.block_size

    @pytest.fixture
    def svc(self, pyramid_request):
        return AESService(pyramid_request.registry.settings["aes_secret"])

    @pytest.fixture
    def AES(self, patch):
        return patch("lms.services.aes.AES")


class TestFactory:
    def test_it(self, pyramid_request, AESService):
        aes_service = factory(sentinel.context, pyramid_request)

        AESService.assert_called_once_with(
            pyramid_request.registry.settings["aes_secret"]
        )
        assert aes_service == AESService.return_value

    @pytest.fixture
    def AESService(self, patch):
        return patch("lms.services.aes.AESService")
