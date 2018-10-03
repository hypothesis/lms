import datetime
import jwt

import pytest

from lms.config import resources


class TestRoot:
    def test_hypothesis_config_contains_one_service_config(self, root):
        assert len(root.hypothesis_config["services"]) == 1

    def test_hypothesis_config_includes_the_api_url(self, root):
        root.hypothesis_config["services"][0]["apiUrl"] == "https://example.com/api"

    def test_hypothesis_config_includes_the_authority(self, root):
        assert root.hypothesis_config["services"][0]["authority"] == "TEST_AUTHORITY"

    def test_hypothesis_config_includes_grant_token(self, root):
        before = int(datetime.datetime.now().timestamp())

        grant_token = root.hypothesis_config["services"][0]["grantToken"]

        claims = jwt.decode(
            grant_token,
            algorithms=["HS256"],
            key="TEST_JWT_CLIENT_SECRET",
            audience="example.com",
        )
        after = int(datetime.datetime.now().timestamp())
        assert claims["iss"] == "TEST_JWT_CLIENT_ID"
        assert claims["sub"] == "acct:75a0b8df844a493bc789385bbbd885@TEST_AUTHORITY"
        assert before <= claims["nbf"] <= after
        assert claims["exp"] > before

    def test_rpc_server_config(self, root):
        assert root.rpc_server_config == {"allowedOrigins": ["http://localhost:5000"]}

    @pytest.fixture
    def root(self, pyramid_request):
        return resources.Root(pyramid_request)
