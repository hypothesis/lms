import json
from datetime import datetime, timedelta
from unittest.mock import Mock, sentinel

import pytest
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from freezegun import freeze_time
from h_matchers import Any

from lms.models import RSAKey
from lms.services.rsa_key import RSAKeyService, factory
from tests import factories


class TestAESService:
    @freeze_time("2022-1-15")
    def test_rotate(self, svc, valid_keys, expired_keys, db_session):
        # Keys created the 10th, max ages of 2 and 4 both expire valid and
        # deleted expired on the 15th.
        target_keys = 5

        svc.rotate(
            target_keys, max_age=timedelta(days=2), max_expired_age=timedelta(days=4)
        )

        assert all((key.expired for key in valid_keys))
        assert not any((key in db_session for key in expired_keys))
        assert db_session.query(RSAKey).filter_by(expired=False).count() == target_keys

    @freeze_time("2022-1-11")
    @pytest.mark.usefixtures("expired_keys")
    def test_rotate_doesnt_expire_valid(self, svc, valid_keys):
        # Keys created the 10th, max age of 2, doesn't expire the keys on the
        # 11th.
        svc.rotate(3, max_age=timedelta(days=2), max_expired_age=timedelta(days=5))

        assert not any((key.expired for key in valid_keys))

    @freeze_time("2022-1-11")
    @pytest.mark.usefixtures("valid_keys")
    def test_rotate_doesnt_delete_recent_expires(self, svc, expired_keys, db_session):
        # Keys created the 10th, max expired age of 5, doesn't delete the keys
        # on the 11th.
        svc.rotate(3, max_age=timedelta(days=2), max_expired_age=timedelta(days=5))
        assert all((key in db_session for key in expired_keys))

    def test_generate(self, svc, aes_service, rsa):
        rsa.generate_private_key.return_value.public_key.return_value.public_numbers.return_value = Mock(
            n=10, e=100
        )

        key = svc.generate()

        # Private key
        rsa.generate_private_key.assert_called_once_with(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )
        aes_service.build_iv.assert_called_once_with()
        rsa.generate_private_key.return_value.private_bytes.assert_called_once_with(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=svc.no_encryption,
        )
        aes_service.encrypt.assert_called_once_with(
            aes_service.build_iv.return_value,
            rsa.generate_private_key.return_value.private_bytes.return_value,
        )
        assert key.private_key == aes_service.encrypt.return_value
        assert key.aes_cipher_iv == aes_service.build_iv.return_value
        # Public key
        assert key.public_key == json.dumps(
            {
                "alg": "RS256",
                "kty": "RSA",
                "n": "Cg",
                "e": "ZA",
            }
        )

    def test_private_key(self, aes_service, svc):
        key = RSAKey(aes_cipher_iv=sentinel.iv, private_key=sentinel.private_key)

        private_key = svc.private_key(key)

        aes_service.decrypt.assert_called_once_with(sentinel.iv, sentinel.private_key)
        assert private_key == aes_service.decrypt.return_value

    def test_get_all_public_jwks(self, svc, valid_keys, expired_keys):
        keys = svc.get_all_public_jwks()

        expected_keys = [
            {"use": "sig", "kid": key.kid, "key": "value"}
            for key in (valid_keys + expired_keys)
        ]
        assert keys == Any.list.containing(expected_keys).only()

    def test_get_random_key(self, svc, valid_keys):
        key = svc.get_random_key()

        assert key in valid_keys

    def test__as_jwk_public_key(self, svc, rsa_key):
        assert svc._as_jwk_public_key(rsa_key) == {  # noqa: SLF001
            "alg": "RS256",
            "kty": "RSA",
            "n": "2BNk2-UPDI3ihR8MXMi11xNzaaS0NiVDTzA7MczlRh9WAqRW3onaCmNgFXmq-hHy1HKIPohMn_N9TvmtrvhTQV_skn4lADYyfxFTsKZkFPJWoOx3sbRJPZVx7HiPaHb72zpTfhwsg5HHa3Sn5Qs8Fybyo33sjbTX1sGZUCq3JGbtEgOii2j19ICS-87AXcMFmCGkaTCFwDoQ38swYDU1YjwhINxx-N5hU19vxA8ZmNexnrpKhvF9C2ejS63xJxMCInfJZFb-Yh2zrzExMLQLpTUEBd0tw1ng66xqkB2LUwr0j-Zdo5_swEepQuOtuLq9omFP345kYIk6IIl0NMcnpQ",
            "e": "AQAB",
        }

    @pytest.fixture
    def valid_keys(self):
        return factories.RSAKey.create_batch(
            size=3,
            public_key='{"key": "value"}',
            created=datetime(2022, 1, 10),
        )

    @pytest.fixture
    def expired_keys(self):
        return factories.RSAKey.create_batch(
            size=3,
            expired=True,
            public_key='{"key": "value"}',
            created=datetime(2022, 1, 10),
        )

    @pytest.fixture
    def svc(self, db_session, aes_service):
        return RSAKeyService(db_session, aes_service)

    @pytest.fixture
    def rsa(self, patch):
        return patch("lms.services.rsa_key.rsa")

    @pytest.fixture
    def rsa_key(self):
        # Taken from the output of generate().private_key
        key_data = b"-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA2BNk2+UPDI3ihR8MXMi11xNzaaS0NiVDTzA7MczlRh9WAqRW\n3onaCmNgFXmq+hHy1HKIPohMn/N9TvmtrvhTQV/skn4lADYyfxFTsKZkFPJWoOx3\nsbRJPZVx7HiPaHb72zpTfhwsg5HHa3Sn5Qs8Fybyo33sjbTX1sGZUCq3JGbtEgOi\ni2j19ICS+87AXcMFmCGkaTCFwDoQ38swYDU1YjwhINxx+N5hU19vxA8ZmNexnrpK\nhvF9C2ejS63xJxMCInfJZFb+Yh2zrzExMLQLpTUEBd0tw1ng66xqkB2LUwr0j+Zd\no5/swEepQuOtuLq9omFP345kYIk6IIl0NMcnpQIDAQABAoIBAAWMdyXVcg3WU+rF\nIBeYeODy/F79YYciOe8ETYGku364PcikfAcyPr6CP3yo5FZ2uqFj51jeit2XQcPG\nK7fHSgRvAex5UrQFcEXTX4goOBnSM+rLsvKSu/tZ0kEQ3H/oGrIa9pUE6xi3pOMY\nlECQiaSMXCVAjdNN9LZfwAyvHocpYf8GFo/NBmf1vheDReFiO9Rpx9QzYOO8G6i7\n26aBIiQOHHd+utXF6UXaOW+CHT0fTUWLbUVeaCIWJWdcFzkTcaVGBdEj+H8wfjb3\nW6xwZ/0b7Nma4z+OB1nQ9mCc6+OVoPRylpjP8KAkqGg3sD0TXdolSxdriKGGCKNv\nBqf0iSECgYEA7mIw1hS0hElhlAZqdMFEc761Kect/8btGOZ8vEoVVea4d7a+NJuZ\n8NKRZ7ROcYZjirE3QXAVgGQZTP9S4XuZITVF5DFsR1jjHSKjO/X8LTjo4WzTH1ol\nAJW6zEC8Wpx8QRwfjPQi5IJfnLf1cAJiLuQzrk+XRNvUUa+Am+cEu0UCgYEA6Ast\ng5R7sHSqHnXlMppPNvJQy4bK70+G2VEJF4nY+yVo8n8l/D5zG83X4feepuUvoiAV\nE9/1DCHUSj/9XJlPpgaA/QSVuSoCzLkVFv3QnwMV82hRr6sBw+QlO0mnGfyE/Xl1\niLKSGhCEqGMXuqvyunViheX/QOIpxnTnVffFUOECgYEAtM+bdTXdOh2iurEnHAnf\nzt8O8Iqd9EzBV8qzP+n9RtuqfXsJyENhvy0oBv3XJfqmE/OZErReSrUiD6n2BntG\nSc7rhUsLcw5zrYyxPXC15uMsmJd/h19Lg6cOOZC8jQn2oTggojwnHyXYObm6m0vj\nhuemX4eVGDCZWaABr77JcvUCgYAWjree+flIPx8mlOlyEOQwgD/weSsTNpTyXVlX\n63OnfoyEPm4P5nZENq+M7QiESvVlel7yLqxgwI0lprDXpqPCjRFPB3oSpQ3enwN4\n17XHL4KbxgFi5WnnhC9GYzOWaCD5jywo3MstM3vh7rgo0nxnOfAY+jHlOdc7zrOK\nfOq2oQKBgQDtSLLelV/u24iHfsOVMO5Wpdytdkls3uG410vlgMteytn682vg4knT\n+0x4M3CnQoZ6l9MpuEFB/a9Ya6kZsL3n3duQwMcOYj9YF5Oj6xzlVTGdTM/+1SFK\nAHCI/NHS3Ap2RljTSiMKpN3eRAdp3KoOJOvMCIHl6MMoRp2bVPgplw==\n-----END RSA PRIVATE KEY-----\n"
        return serialization.load_pem_private_key(key_data, None)


class TestFactory:
    def test_it(self, pyramid_request, RSAKeyService, aes_service, db_session):
        rsa_key_service = factory(sentinel.context, pyramid_request)

        RSAKeyService.assert_called_once_with(db_session, aes_service)
        assert rsa_key_service == RSAKeyService.return_value

    @pytest.fixture
    def RSAKeyService(self, patch):
        return patch("lms.services.rsa_key.RSAKeyService")
