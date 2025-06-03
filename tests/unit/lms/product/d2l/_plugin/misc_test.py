from unittest.mock import sentinel

import pytest

from lms.product.d2l._plugin.misc import D2LMiscPlugin


class TestD2LMiscPlugin:
    def test_prompt_for_gradable_returns_false_for_lti_1p0(self, application_instance):
        plugin = D2LMiscPlugin()
        assert plugin.deep_linking_prompt_for_gradable(application_instance) is False

    @pytest.mark.parametrize("feature_flag", [True, False])
    def test_prompt_for_gradable_returns_setting_for_lti_13(
        self, lti_v13_application_instance, feature_flag
    ):
        lti_v13_application_instance.settings.set(
            "hypothesis", "prompt_for_gradable", feature_flag
        )
        plugin = D2LMiscPlugin()

        assert (
            plugin.deep_linking_prompt_for_gradable(lti_v13_application_instance)
            == feature_flag
        )

    def test_deep_linking_prompt_for_title(self, plugin):
        assert plugin.deep_linking_prompt_for_title

    def test_get_ltia_aud_claim(self, plugin):
        assert (
            plugin.get_ltia_aud_claim(sentinel.registration)
            == "https://api.brightspace.com/auth/token"
        )

    def test_factory(self, pyramid_request):
        plugin = D2LMiscPlugin.factory(sentinel.context, pyramid_request)
        assert isinstance(plugin, D2LMiscPlugin)

    @pytest.fixture
    def plugin(self):
        return D2LMiscPlugin()
