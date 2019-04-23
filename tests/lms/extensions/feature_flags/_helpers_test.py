import jwt
import pytest
from pyramid.httpexceptions import HTTPFound

from lms.extensions.feature_flags._exceptions import SettingError
from lms.extensions.feature_flags._helpers import (
    FeatureFlagsCookieHelper,
    JWTCookieHelper,
)


class TestFeatureFlagsCookieHelper:
    def test_set_cookie_sets_the_cookie_from_the_request_params(
        self, pyramid_request, JWTCookieHelper, jwt_cookie_helper
    ):
        flags = pyramid_request.params = {"test_flag_one": True, "test_flag_two": False}
        response = HTTPFound()
        helper = FeatureFlagsCookieHelper(pyramid_request)

        helper.set_cookie(response)

        JWTCookieHelper.assert_called_once_with("feature_flags", pyramid_request)
        jwt_cookie_helper.set.assert_called_once_with(response, flags)

    def test_set_cookie_omits_disallowed_feature_flags(
        self, pyramid_request, jwt_cookie_helper
    ):
        flags = pyramid_request.params = {
            "test_flag_one": True,
            "test_flag_two": False,
            "disallowed_flag": True,
        }
        helper = FeatureFlagsCookieHelper(pyramid_request)

        helper.set_cookie(HTTPFound())

        assert jwt_cookie_helper.set.call_args[0][1] == {
            "test_flag_one": True,
            "test_flag_two": False,
        }

    def test_get_gets_the_flag_from_the_cookie(
        self, pyramid_request, JWTCookieHelper, jwt_cookie_helper
    ):
        jwt_cookie_helper.get.return_value = {"test_flag_one": True}
        helper = FeatureFlagsCookieHelper(pyramid_request)

        flag = helper.get("test_flag_one")

        JWTCookieHelper.assert_called_once_with("feature_flags", pyramid_request)
        jwt_cookie_helper.get.assert_called_once_with()
        assert flag is True

    def test_get_returns_False_if_flag_is_toggled_off_in_cookie(
        self, pyramid_request, JWTCookieHelper, jwt_cookie_helper
    ):
        jwt_cookie_helper.get.return_value = {"test_flag_one": False}
        helper = FeatureFlagsCookieHelper(pyramid_request)

        assert helper.get("test_flag_one") is False

    def test_get_omits_disallowed_flags(self, jwt_cookie_helper, pyramid_request):
        jwt_cookie_helper.get.return_value = {"disallowed_flag": True}
        helper = FeatureFlagsCookieHelper(pyramid_request)

        assert helper.get("disallowed_flag") is False

    def test_get_all_gets_all_the_flags_from_the_cookie(
        self, pyramid_request, JWTCookieHelper, jwt_cookie_helper
    ):
        pyramid_request.params = jwt_cookie_helper.get.return_value = {
            "test_flag_one": True,
            "test_flag_two": False,
        }
        helper = FeatureFlagsCookieHelper(pyramid_request)

        returned_flags = helper.get_all()

        JWTCookieHelper.assert_called_once_with("feature_flags", pyramid_request)
        jwt_cookie_helper.get.assert_called_once_with()
        assert returned_flags == {"test_flag_one": True, "test_flag_two": False}

    def test_get_all_omits_disallowed_flags(self, pyramid_request, jwt_cookie_helper):
        pyramid_request.params = jwt_cookie_helper.get.return_value = {
            "test_flag_one": True,
            "test_flag_two": False,
            "disallowed_flag": True,
        }
        helper = FeatureFlagsCookieHelper(pyramid_request)

        assert helper.get_all() == {"test_flag_one": True, "test_flag_two": False}

    def test_when_theres_no_flags_allowed_set_turns_off_all_flags(
        self, pyramid_request, jwt_cookie_helper
    ):
        pyramid_request.registry.settings["feature_flags_allowed_in_cookie"] = ""
        pyramid_request.params = {"test_flag_one": True, "test_flag_two": False}
        response = HTTPFound()
        helper = FeatureFlagsCookieHelper(pyramid_request)

        helper.set_cookie(response)

        jwt_cookie_helper.set.assert_called_once_with(response, {})

    def test_when_theres_no_flags_allowed_get_always_returns_False(
        self, pyramid_request, jwt_cookie_helper
    ):
        pyramid_request.registry.settings["feature_flags_allowed_in_cookie"] = ""
        jwt_cookie_helper.get.return_value = {"test_flag_one": True}
        helper = FeatureFlagsCookieHelper(pyramid_request)

        assert helper.get("test_flag_one") is False

    def test_when_theres_no_flags_allowed_get_all_returns_an_empty_dict(
        self, pyramid_request, jwt_cookie_helper
    ):
        pyramid_request.registry.settings["feature_flags_allowed_in_cookie"] = ""
        pyramid_request.params = jwt_cookie_helper.get.return_value = {
            "test_flag_one": True,
            "test_flag_two": False,
        }
        helper = FeatureFlagsCookieHelper(pyramid_request)

        assert helper.get_all() == {}

    @pytest.fixture
    def pyramid_config(self, pyramid_config):
        pyramid_config.registry.settings[
            "feature_flags_allowed_in_cookie"
        ] = "test_flag_one test_flag_two"
        return pyramid_config

    @pytest.fixture(autouse=True)
    def JWTCookieHelper(self, patch):
        return patch("lms.extensions.feature_flags._helpers.JWTCookieHelper")

    @pytest.fixture
    def jwt_cookie_helper(self, JWTCookieHelper):
        return JWTCookieHelper.return_value


class TestJWTCookieHelper:
    def test_it_crashes_if_no_feature_flags_cookie_secret(self, pyramid_request):
        del pyramid_request.registry.settings["feature_flags_cookie_secret"]

        with pytest.raises(
            SettingError,
            match="The feature_flags_cookie_secret deployment setting is required",
        ):
            JWTCookieHelper("test_cookie_name", pyramid_request)

    def test_set_encodes_the_payload_in_the_cookie(self, pyramid_request):
        original_payload = {"test_key": "test_value"}
        helper = JWTCookieHelper("test_cookie_name", pyramid_request)
        response = HTTPFound()

        helper.set(response, original_payload)

        cookie = response.headers["Set-Cookie"].split(";")[0].split("=")[1]
        decoded_payload = jwt.decode(cookie, "test_secret", algorithms=["HS256"])
        assert decoded_payload == original_payload

    def test_get_returns_the_decoded_payload(self, pyramid_request):
        original_payload = {"test_key": "test_value"}
        encoded_payload = jwt.encode(original_payload, "test_secret", algorithm="HS256")
        pyramid_request.cookies["test_cookie_name"] = encoded_payload
        helper = JWTCookieHelper("test_cookie_name", pyramid_request)

        assert helper.get() == original_payload

    def test_get_returns_an_empty_dict_if_the_cookie_is_invalid(self, pyramid_request):
        pyramid_request.cookies["test_cookie_name"] = "invalid"
        helper = JWTCookieHelper("test_cookie_name", pyramid_request)

        assert helper.get() == {}

    def test_get_returns_an_empty_dict_if_theres_no_cookie(self, pyramid_request):
        helper = JWTCookieHelper("test_cookie_name", pyramid_request)

        assert helper.get() == {}

    def test_that_set_and_get_work_together(self, pyramid_request):
        original_payload = {"test_key": "test_value"}
        helper = JWTCookieHelper("test_cookie_name", pyramid_request)
        response = HTTPFound()

        helper.set(response, original_payload)

        cookie = response.headers["Set-Cookie"].split(";")[0].split("=")[1]
        pyramid_request.cookies["test_cookie_name"] = cookie

        assert helper.get() == original_payload

    @pytest.fixture(autouse=True)
    def pyramid_config(self, pyramid_config):
        pyramid_config.registry.settings["feature_flags_cookie_secret"] = "test_secret"
        return pyramid_config
