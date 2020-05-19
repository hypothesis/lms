from unittest import mock

import pytest
from pyramid.request import apply_request_extensions

from lms.extensions.feature_flags import includeme


class TestIncludeMe:
    def test_it_creates_the_feature_flags_object(self, pyramid_config, FeatureFlags):
        includeme(pyramid_config)

        FeatureFlags.assert_called_once_with()

    def test_feature(self, feature_flags, pyramid_config, pyramid_request):
        includeme(pyramid_config)
        apply_request_extensions(pyramid_request)

        pyramid_request.feature("test_feature")

        feature_flags.flag_is_active.assert_called_once_with(
            pyramid_request, "test_feature"
        )

    def test_add_feature_flag_providers(self, pyramid_config, feature_flags):
        includeme(pyramid_config)

        pyramid_config.add_feature_flag_providers(
            mock.sentinel.provider_1, mock.sentinel.provider_2
        )

        feature_flags.add_providers.assert_called_once_with(
            mock.sentinel.provider_1, mock.sentinel.provider_2
        )


@pytest.fixture(autouse=True)
def FeatureFlags(patch):
    return patch("lms.extensions.feature_flags.FeatureFlags")


@pytest.fixture
def feature_flags(FeatureFlags):
    return FeatureFlags.return_value
