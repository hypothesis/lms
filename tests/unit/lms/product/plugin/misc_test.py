from unittest.mock import sentinel

import pytest

from lms.product.plugin.misc import MiscPlugin
from tests import factories


class TestMiscPlugin:
    @pytest.mark.parametrize(
        "service_url,expected", [(None, False), (sentinel.service_url, True)]
    )
    def test_is_assignment_gradable(
        self, plugin, pyramid_request, service_url, expected
    ):
        pyramid_request.lti_params["lis_outcome_service_url"] = service_url

        assert plugin.is_assignment_gradable(pyramid_request.lti_params) == expected

    def test_get_ltia_aud_claim(self, plugin, lti_registration):
        assert plugin.get_ltia_aud_claim(lti_registration) == lti_registration.token_url

    @pytest.fixture
    def lti_registration(self):
        return factories.LTIRegistration()

    @pytest.fixture
    def plugin(self):
        return MiscPlugin()
