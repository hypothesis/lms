from unittest.mock import create_autospec

import pytest
from hubspot import HubSpot

from lms.services.hubspot._client import HubSpotClient


class TestHubSpotClient:
    def test_get_companies(self, api_client, svc):
        companies = list(svc.get_companies())

        api_client.crm.companies.get_all.assert_called_once_with(
            properties=[
                "hs_object_id",
                "name",
                "lms_organization_id",
                "current_deal__services_start",
                "current_deal__services_end",
            ]
        )
        assert companies == list(api_client.crm.companies.get_all.return_value)

    @pytest.fixture
    def api_client(self):
        return create_autospec(HubSpot, spec_set=True, instance=True)

    @pytest.fixture
    def svc(self, api_client):
        return HubSpotClient(api_client=api_client)
