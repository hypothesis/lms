from unittest.mock import sentinel

import jwt
import pytest
from pyramid.httpexceptions import HTTPFound

from lms.extensions.feature_flags._exceptions import SettingError
from lms.extensions.feature_flags._helpers import (
    FeatureFlagsCookieHelper,
    JWTCookieHelper,
    as_tristate,
)


class TestAsTristate:
    @pytest.mark.parametrize(
        "value,expected_value",
        (
            # Truthy
            (True, True),
            ("True", True),
            ("true", True),
            ("1", True),
            (1, True),
            # Falsy
            (False, False),
            ("False", False),
            ("false", False),
            ("0", False),
            (0, False),
            # None
            ("", None),
            (None, None),
            ("None", None),
            ("none", None),
        ),
    )
    def test_it(self, value, expected_value):
        assert as_tristate(value) == expected_value


class TestFeatureFlagsCookieHelper:
    def test_get_all(self, cookie_helper):
        flags = cookie_helper.get_all()

        assert flags == {"flag_one": True, "flag_two": False}

    @pytest.mark.parametrize(
        "flag,expected_value",
        (("flag_one", True), ("flag_two", False), ("flag_three", None)),
    )
    def test_get(self, cookie_helper, flag, expected_value):
        assert cookie_helper.get(flag) == expected_value

    def test_set_cookie(self, cookie_helper, jwt_cookie_helper, pyramid_request):
        pyramid_request.params = {
            "flag_one": "false",
            "flag_two": "true",
            "flag_three": "true",
        }

        cookie_helper.set_cookie(sentinel.response)

        jwt_cookie_helper.set.assert_called_once_with(
            sentinel.response, {"flag_one": False, "flag_two": True}
        )

    @pytest.fixture
    def cookie_helper(self, pyramid_request):
        return FeatureFlagsCookieHelper(pyramid_request)

    @pytest.fixture
    def pyramid_config(self, pyramid_config):
        pyramid_config.registry.settings[
            "feature_flags_allowed_in_cookie"
        ] = "flag_one flag_two"
        return pyramid_config

    @pytest.fixture(autouse=True)
    def jwt_cookie_helper(self, patch):
        JWTCookieHelper = patch("lms.extensions.feature_flags._helpers.JWTCookieHelper")

        JWTCookieHelper.return_value.get.return_value = {
            "flag_one": 1,
            "flag_two": "false",
            "flag_three": "not in feature_flags_allowed_in_cookie",
        }

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
