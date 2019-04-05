import pytest

from lms.subscribers._template_environment import _add_js_config


class TestJSConfig:
    def test_it_adds_the_urls_to_the_template_environment(self, pyramid_request):
        event = {"request": pyramid_request}

        _add_js_config(event)

        # urls is an empty dict for now!
        assert event["js_config"]["urls"] == {}

    def test_if_theres_an_lti_user_it_adds_the_authorization_param_to_the_template_environment(
        self, bearer_token_schema, BearerTokenSchema, pyramid_request
    ):
        event = {"request": pyramid_request}

        _add_js_config(event)

        BearerTokenSchema.assert_called_once_with(pyramid_request)
        assert (
            event["js_config"]["authorization_param"]
            == bearer_token_schema.authorization_param.return_value
        )

    def test_if_theres_no_lti_user_it_doesnt_add_the_authorization_param_to_the_template_environment(
        self, BearerTokenSchema, pyramid_request
    ):
        pyramid_request.lti_user = None
        event = {"request": pyramid_request}

        _add_js_config(event)

        BearerTokenSchema.assert_not_called()
        assert "authorization_param" not in event["js_config"]

    @pytest.fixture(autouse=True)
    def BearerTokenSchema(self, patch):
        return patch("lms.subscribers._template_environment.BearerTokenSchema")

    @pytest.fixture
    def bearer_token_schema(self, BearerTokenSchema):
        return BearerTokenSchema.return_value
