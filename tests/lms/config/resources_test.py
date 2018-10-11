import datetime
import jwt

import pytest
from pyramid.httpexceptions import HTTPBadRequest

from lms.config import resources


class TestLTILaunch:
    def test_it_raises_if_no_lti_params_for_request(self, pyramid_request, lti_params_for):
        lti_params_for.side_effect = HTTPBadRequest()

        with pytest.raises(HTTPBadRequest):
            resources.LTILaunch(pyramid_request)

    def test_hypothesis_config_contains_one_service_config(self, lti_launch):
        assert len(lti_launch.hypothesis_config["services"]) == 1

    def test_hypothesis_config_includes_the_api_url(self, lti_launch):
        assert lti_launch.hypothesis_config["services"][0]["apiUrl"] == "https://example.com/api/"

    def test_hypothesis_config_includes_the_authority(self, lti_launch):
        assert lti_launch.hypothesis_config["services"][0]["authority"] == "TEST_AUTHORITY"

    def test_hypothesis_config_includes_grant_token(self, lti_launch):
        before = int(datetime.datetime.now().timestamp())

        grant_token = lti_launch.hypothesis_config["services"][0]["grantToken"]

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
        self, pyramid_request, lti_launch, lti_params_for
    ):
        lti_params_for.return_value.update({"oauth_consumer_key": "some_other_key"})
        assert lti_launch.hypothesis_config == {}

    def test_rpc_server_config(self, lti_launch):
        assert lti_launch.rpc_server_config == {"allowedOrigins": ["http://localhost:5000"]}

    @pytest.fixture
    def lti_launch(self, pyramid_request):
        return resources.LTILaunch(pyramid_request)

    @pytest.fixture(autouse=True)
    def lti_params_for(self, patch):
        lti_params_for = patch("lms.config.resources.lti_params_for")
        lti_params_for.return_value = {
            # A valid oauth_consumer_key (matches one for which the
            # provisioning features are enabled).
            "oauth_consumer_key": "Hypothesise3f14c1f7e8c89f73cefacdd1d80d0ef",
        }
        return lti_params_for

    @pytest.fixture(autouse=True)
    def util(self, patch):
        util = patch("lms.config.resources.util")
        util.generate_username.return_value = "75a0b8df844a493bc789385bbbd885"
        return util
