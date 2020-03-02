import datetime
from unittest import mock

import jwt
import pytest
from pyramid.httpexceptions import HTTPBadRequest

from lms.resources import LTILaunchResource
from lms.resources._js_config import JSConfig
from lms.values import HUser


class TestJSConfig:
    """General unit tests for JSConfig."""

    def test_it_is_mutable(self, config):
        config.update({"a_key": "a_value"})

        assert config["a_key"] == "a_value"


class TestJSConfigAuthToken:
    """Unit tests for the "authToken" sub-dict of JSConfig."""

    def test_it(
        self, authToken, bearer_token_schema, BearerTokenSchema, pyramid_request
    ):
        BearerTokenSchema.assert_called_once_with(pyramid_request)
        bearer_token_schema.authorization_param.assert_called_once_with(
            pyramid_request.lti_user
        )
        assert authToken == bearer_token_schema.authorization_param.return_value

    @pytest.mark.usefixtures("no_lti_user")
    def test_it_is_None_for_non_lti_users(self, authToken):
        assert authToken is None

    @pytest.fixture
    def authToken(self, config):
        return config["authToken"]


class TestJSConfigDebug:
    """Unit tests for the "debug" sub-dict of JSConfig."""

    def test_it_contains_debugging_info_about_the_users_role(self, config):
        assert "role:learner" in config["tags"]

    @pytest.mark.usefixtures("no_lti_user")
    def test_its_empty_if_theres_no_lti_user(self, config):
        assert config == {}

    @pytest.fixture
    def config(self, config):
        return config["debug"]


class TestJSConfigHypothesisClient:
    """Unit tests for the "hypothesisClient" sub-dict of JSConfig."""

    def test_it_contains_one_service_config(self, config):
        assert len(config["services"]) == 1

    def test_it_includes_the_api_url(self, config):
        assert config["services"][0]["apiUrl"] == "https://example.com/api/"

    def test_it_includes_the_authority(self, config):
        assert config["services"][0]["authority"] == "TEST_AUTHORITY"

    def test_it_disables_share_links(self, config):
        assert config["services"][0]["enableShareLinks"] is False

    def test_it_includes_grant_token(self, config):
        before = int(datetime.datetime.now().timestamp())

        grant_token = config["services"][0]["grantToken"]

        claims = jwt.decode(
            grant_token,
            algorithms=["HS256"],
            key="TEST_JWT_CLIENT_SECRET",
            audience="example.com",
        )
        after = int(datetime.datetime.now().timestamp())
        assert claims["iss"] == "TEST_JWT_CLIENT_ID"
        assert claims["sub"] == "acct:example_username@TEST_AUTHORITY"
        assert before <= claims["nbf"] <= after
        assert claims["exp"] > before

    def test_it_includes_the_group(self, config):
        groups = config["services"][0]["groups"]

        assert groups == ["example_groupid"]

    @pytest.mark.usefixtures("provisioning_disabled")
    def test_it_is_empty_if_provisioning_feature_is_disabled(self, config):
        assert config == {}

    def test_it_is_mutable(self, config):
        config.update({"a_key": "a_value"})

        assert config["a_key"] == "a_value"

    @pytest.mark.parametrize(
        "context_property", ["provisioning_enabled", "h_user", "h_groupid"]
    )
    def test_it_raises_if_a_context_property_raises(
        self, context, context_property, pyramid_request
    ):
        # Make reading context.<context_property> raise HTTPBadRequest.
        setattr(
            type(context),
            context_property,
            mock.PropertyMock(side_effect=HTTPBadRequest("example error message")),
        )

        with pytest.raises(HTTPBadRequest, match="example error message"):
            JSConfig(context, pyramid_request)._hypothesis_client

    @pytest.fixture
    def config(self, config):
        return config["hypothesisClient"]


class TestJSConfigRPCServer:
    """Unit tests for the "rpcServer" sub-dict of JSConfig."""

    def test_it(self, config):
        assert config == {"allowedOrigins": ["http://localhost:5000"]}

    @pytest.fixture
    def config(self, config):
        return config["rpcServer"]


class TestJSConfigURLs:
    """Unit tests for the "urls" sub-dict of JSConfig."""

    def test_it(self, config):
        assert config == {}

    @pytest.fixture
    def config(self, config):
        return config["urls"]


@pytest.fixture(autouse=True)
def BearerTokenSchema(patch):
    return patch("lms.resources._js_config.BearerTokenSchema")


@pytest.fixture
def bearer_token_schema(BearerTokenSchema):
    return BearerTokenSchema.return_value


@pytest.fixture
def js_config(context, pyramid_request):
    return JSConfig(context, pyramid_request)


@pytest.fixture
def config(js_config):
    return js_config.config


@pytest.fixture
def context():
    return mock.create_autospec(
        LTILaunchResource,
        spec_set=True,
        instance=True,
        h_user=HUser("TEST_AUTHORITY", "example_username"),
        h_groupid="example_groupid",
    )


@pytest.fixture
def no_lti_user(pyramid_request):
    """Modify the pyramid_request fixture so that request.lti_user is None."""
    pyramid_request.lti_user = None


@pytest.fixture
def provisioning_disabled(context):
    """Modify context so that context.provisioning_enabled is False."""
    context.provisioning_enabled = False
