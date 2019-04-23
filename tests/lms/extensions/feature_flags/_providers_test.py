from unittest import mock

import pytest

from lms.extensions.feature_flags import config_file_provider
from lms.extensions.feature_flags import envvar_provider
from lms.extensions.feature_flags import query_string_provider
from lms.extensions.feature_flags import cookie_provider


class TestConfigFileProvider:
    @pytest.mark.parametrize(
        "settings,result",
        [
            ({"feature_flags.test_feature": "true"}, True),
            ({"feature_flags.test_feature": "false"}, False),
            ({}, None),
        ],
    )
    def test_it(self, pyramid_request, settings, result):
        pyramid_request.registry.settings.update(settings)
        assert config_file_provider(pyramid_request, "test_feature") == result


class TestEnvVarProvider:
    @pytest.mark.parametrize(
        "envvars,result",
        [
            ({"FEATURE_FLAG_TEST_FEATURE": "true"}, True),
            ({"FEATURE_FLAG_TEST_FEATURE": "false"}, False),
            ({}, None),
        ],
    )
    def test_it(self, pyramid_request, envvars, result, os):
        os.environ.update(envvars)
        assert envvar_provider(pyramid_request, "test_feature") == result

    @pytest.fixture(autouse=True)
    def os(self, patch):
        os = patch("lms.extensions.feature_flags._providers.os")
        os.environ = {}
        return os


class TestCookieProvider:
    def test_it(self, FeatureFlagsCookieHelper):
        result = cookie_provider(mock.sentinel.request, "test_feature")

        FeatureFlagsCookieHelper.assert_called_once_with(mock.sentinel.request)
        FeatureFlagsCookieHelper.return_value.get.assert_called_once_with(
            "test_feature"
        )
        assert result == FeatureFlagsCookieHelper.return_value.get.return_value


class TestQueryStringProvider:
    @pytest.mark.parametrize(
        "query_params,result",
        [
            ({"feature_flags.test_feature": "true"}, True),
            ({"feature_flags.test_feature": "false"}, False),
            ({}, None),
        ],
    )
    def test_it(self, pyramid_request, query_params, result):
        pyramid_request.GET.update(query_params)
        assert query_string_provider(pyramid_request, "test_feature") == result


@pytest.fixture(autouse=True)
def FeatureFlagsCookieHelper(patch):
    return patch("lms.extensions.feature_flags._providers.FeatureFlagsCookieHelper")
