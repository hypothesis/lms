from unittest.mock import sentinel

import pytest

from lms.models import LTIParams
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

    def test_get_document_url_with_assignment_in_db_existing_assignment(
        self, plugin, pyramid_request, assignment_service
    ):
        assignment_service.get_assignment.return_value = factories.Assignment(
            document_url=sentinel.document_url
        )
        pyramid_request.lti_params["resource_link_id"] = sentinel.link_id

        result = plugin.get_document_url(pyramid_request)

        assignment_service.get_assignment.assert_called_once_with(
            tool_consumer_instance_guid=pyramid_request.lti_params[
                "tool_consumer_instance_guid"
            ],
            resource_link_id=sentinel.link_id,
        )
        assert result == sentinel.document_url

    def test_get_document_url_with_assignment_in_db_copied_assignment(
        self, plugin, pyramid_request, assignment_service
    ):
        assignment_service.get_assignment.return_value = None
        assignment_service.get_copied_from_assignment.return_value = (
            factories.Assignment(document_url=sentinel.document_url)
        )
        pyramid_request.lti_params["resource_link_id"] = sentinel.link_id

        result = plugin.get_document_url(pyramid_request)

        assignment_service.get_assignment.assert_called_once_with(
            tool_consumer_instance_guid=pyramid_request.lti_params[
                "tool_consumer_instance_guid"
            ],
            resource_link_id=sentinel.link_id,
        )
        assignment_service.get_copied_from_assignment.assert_called_once_with(
            pyramid_request.lti_params
        )

        assert result == sentinel.document_url

    @pytest.fixture
    def lti_registration(self):
        return factories.LTIRegistration()

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.lti_params = LTIParams({"tool_consumer_instance_guid": "guid"})
        return pyramid_request

    @pytest.fixture
    def plugin(self):
        return MiscPlugin()
