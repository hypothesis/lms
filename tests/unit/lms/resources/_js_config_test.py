import datetime
from unittest import mock

import jwt
import pytest
from pyramid.httpexceptions import HTTPBadRequest

from lms.resources import LTILaunchResource
from lms.resources._js_config import JSConfig
from lms.services import HAPIError
from lms.values import HUser


class TestJSConfig:
    """General unit tests for JSConfig."""

    def test_auth_url(self, config):
        assert config["authUrl"] == "http://example.com/api/canvas/authorize"

    def test_it_is_mutable(self, config):
        config.update({"a_key": "a_value"})

        assert config["a_key"] == "a_value"

    def test_enable_content_item_selection_mode(self, js_config):
        js_config.enable_content_item_selection_mode()

        assert js_config.config["mode"] == "content-item-selection"


class TestAddCanvasFileID:
    """Unit tests for JSConfig.add_canvas_file_id()."""

    def test_it_adds_the_via_url_callback_url(self, js_config):
        js_config.add_canvas_file_id("example_canvas_file_id")

        assert (
            js_config.config["urls"]["via_url_callback"]
            == "http://example.com/api/canvas/files/example_canvas_file_id/via_url"
        )

    def test_it_sets_the_canvas_file_id(self, js_config):
        js_config.add_canvas_file_id("example_canvas_file_id")

        assert (
            js_config.config["submissionParams"]["canvas_file_id"]
            == "example_canvas_file_id"
        )


class TestAddDocumentURL:
    """Unit tests for JSConfig.add_document_url()."""

    def test_it_adds_the_via_url(self, js_config, pyramid_request, via_url):
        js_config.add_document_url("example_document_url")

        via_url.assert_called_once_with(pyramid_request, "example_document_url")
        assert js_config.config["urls"]["via_url"] == via_url.return_value

    def test_it_sets_the_document_url(self, js_config):
        js_config.add_document_url("example_document_url")

        assert (
            js_config.config["submissionParams"]["document_url"]
            == "example_document_url"
        )


class TestAddCanvasFileIDAddDocumentURLCommon:
    """Tests common to both add_canvas_file_id() and add_document_url()."""

    def test_it_sets_the_canvas_submission_params(self, method, js_config):
        method("canvas_file_id_or_document_url")

        assert js_config.config["submissionParams"]["h_username"] == "example_username"
        assert (
            js_config.config["submissionParams"]["lis_outcome_service_url"]
            == "example_lis_outcome_service_url"
        )
        assert (
            js_config.config["submissionParams"]["lis_result_sourcedid"]
            == "example_lis_result_sourcedid"
        )

    def test_it_doesnt_set_the_canvas_submission_params_if_the_LMS_isnt_Canvas(
        self, context, method, js_config
    ):
        context.is_canvas = False

        method("canvas_file_id_or_document_url")

        assert "submissionParams" not in js_config.config

    def test_it_doesnt_set_the_canvas_submission_params_if_theres_no_lis_result_sourcedid(
        self, method, js_config, pyramid_request
    ):
        del pyramid_request.params["lis_result_sourcedid"]

        method("canvas_file_id_or_document_url")

        assert "submissionParams" not in js_config.config

    def test_it_doesnt_set_the_canvas_submission_params_if_theres_no_lis_outcome_service_url(
        self, method, js_config, pyramid_request
    ):
        del pyramid_request.params["lis_outcome_service_url"]

        method("canvas_file_id_or_document_url")

        assert "submissionParams" not in js_config.config

    def test_it_raises_if_context_h_user_raises(self, context, method):
        # Make reading context.h_user raise HTTPBadRequest.
        setattr(
            type(context),
            "h_user",
            mock.PropertyMock(side_effect=HTTPBadRequest("example error message")),
        )

        with pytest.raises(HTTPBadRequest, match="example error message"):
            method("canvas_file_id_or_document_url")

    @pytest.fixture(params=["add_canvas_file_id", "add_document_url"])
    def method(self, js_config, request):
        """Return the method to be tested."""
        return getattr(js_config, request.param)


class TestMaybeSetFocusedUser:
    def test_it_does_nothing_if_theres_no_focused_user_param(
        self, js_config, pyramid_request
    ):
        del pyramid_request.params["focused_user"]

        js_config.maybe_set_focused_user()

        assert "focus" not in js_config.config["hypothesisClient"]

    def test_it_sets_the_focused_user_if_theres_a_focused_user_param(
        self, h_api, js_config
    ):
        js_config.maybe_set_focused_user()

        # It gets the display name from the h API.
        h_api.get_user.assert_called_once_with("example_h_username")
        # It sets the focused user.
        assert js_config.config["hypothesisClient"]["focus"] == {
            "user": {
                "username": "example_h_username",
                "displayName": "example_h_display_name",
            },
        }

    def test_display_name_falls_back_to_a_default_value(self, h_api, js_config):
        h_api.get_user.side_effect = HAPIError()

        js_config.maybe_set_focused_user()

        assert (
            js_config.config["hypothesisClient"]["focus"]["user"]["displayName"]
            == "(Couldn't fetch student name)"
        )

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.params["focused_user"] = "example_h_username"
        return pyramid_request


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
        assert not config["services"][0]["enableShareLinks"]

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
            # pylint:disable=expression-not-assigned,protected-access
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


pytestmark = pytest.mark.usefixtures("h_api")


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
        is_canvas=True,
    )


@pytest.fixture
def no_lti_user(pyramid_request):
    """Modify the pyramid_request fixture so that request.lti_user is None."""
    pyramid_request.lti_user = None


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.params["lis_result_sourcedid"] = "example_lis_result_sourcedid"
    pyramid_request.params[
        "lis_outcome_service_url"
    ] = "example_lis_outcome_service_url"
    return pyramid_request


@pytest.fixture
def provisioning_disabled(context):
    """Modify context so that context.provisioning_enabled is False."""
    context.provisioning_enabled = False


@pytest.fixture(autouse=True)
def via_url(patch):
    return patch("lms.resources._js_config.via_url")
