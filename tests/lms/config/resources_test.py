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

    def test_hypothesis_config_is_empty_if_provisioning_feature_is_disabled(
        self, pyramid_request, root
    ):
        pyramid_request.params.update({"oauth_consumer_key": "some_other_key"})
        assert root.hypothesis_config == {}

    def test_rpc_server_config(self, root):
        assert root.rpc_server_config == {"allowedOrigins": ["http://localhost:5000"]}

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.params.update(
            {
                # A valid oauth_consumer_key (matches one for which the
                # provisioning features are enabled).
                "oauth_consumer_key": "Hypothesise3f14c1f7e8c89f73cefacdd1d80d0ef"
            }
        )
        return pyramid_request

    @pytest.fixture
    def root(self, pyramid_request):
        return resources.Root(pyramid_request)
