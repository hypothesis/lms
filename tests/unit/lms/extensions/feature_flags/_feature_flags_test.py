from unittest import mock

import pytest

from lms.extensions.feature_flags._feature_flags import FeatureFlags


def true_provider(_request, _feature_flag_name):
    """Return True for any given feature flag name."""
    return True


def false_provider(_request, _feature_flag_name):
    """Return False for any given feature flag name."""
    return False


def none_provider(_request, _feature_flag_name):
    """Return None for any given feature flag name."""
    return None


class TestFeatureFlags:
    @pytest.mark.parametrize(
        "providers,result",
        [
            ([], False),
            ([true_provider], True),
            ([false_provider], False),
            ([false_provider, true_provider], True),
            ([true_provider, false_provider], False),
            ([true_provider, none_provider], True),
            ([none_provider], False),
            ([none_provider, none_provider], False),
        ],
    )
    def test_it(self, pyramid_request, providers, result):
        feature_flags = FeatureFlags()
        feature_flags.add_providers(*providers)

        assert feature_flags.flag_is_active(pyramid_request, "test_flag") == result

    def test_it_calls_providers_with_request_and_flag(self, pyramid_request):
        feature_flags = FeatureFlags()
        provider_1 = mock.MagicMock()
        provider_2 = mock.MagicMock()
        feature_flags.add_provider(provider_1)
        feature_flags.add_provider(provider_2)

        feature_flags.flag_is_active(pyramid_request, "test_flag")

        provider_1.assert_called_once_with(pyramid_request, "test_flag")
        provider_2.assert_called_once_with(pyramid_request, "test_flag")
