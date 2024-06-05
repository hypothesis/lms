from datetime import date, datetime
from unittest.mock import Mock, create_autospec, sentinel

import pytest

from lms.models import HubSpotCompany
from lms.services.hubspot import HubSpotService
from lms.services.hubspot._client import HubSpotClient
from lms.services.hubspot.service import date_or_timestamp
from tests import factories


class TestHubSpotService:
    def test_get_company(self, svc):
        org = factories.Organization()
        factories.HubSpotCompany(lms_organization_id=org.public_id)

        assert svc.get_company(org.public_id)

    def test_get_companies_with_active_deals(self, svc):
        # Companies that map to the same org, they should be ignored
        org = factories.Organization()
        factories.HubSpotCompany(lms_organization_id=org.public_id)
        factories.HubSpotCompany(lms_organization_id=org.public_id)
        # Company with deal outside the time period
        factories.HubSpotCompany(
            lms_organization_id=factories.Organization().public_id,
            current_deal_services_start=date(2022, 1, 1),
            current_deal_services_end=date(2022, 12, 31),
        )
        company = factories.HubSpotCompany(
            lms_organization_id=factories.Organization().public_id,
            current_deal_services_start=date(2023, 1, 1),
            current_deal_services_end=date(2023, 12, 31),
        )

        assert svc.get_companies_with_active_deals(date(2023, 2, 1)) == [company]

    def test_get_company_multiple_mapping(self, svc):
        org = factories.Organization()
        factories.HubSpotCompany(lms_organization_id=org.public_id)
        factories.HubSpotCompany(lms_organization_id=org.public_id)

        assert not svc.get_company(org.public_id)

    def test_refresh_companies(self, svc, hubspot_api_client, db_session):
        hubspot_api_client.get_companies.return_value = [
            Mock(properties={"lms_organization_id": None}),  # No org ID
            # Org in another region
            Mock(properties={"lms_organization_id": "es.org.XXX"}),
            Mock(
                properties={
                    "lms_organization_id": "us.org.1",
                    "name": "COMPANY",
                    "hs_object_id": 100,
                    "current_deal__services_start": "2024-01-01",
                    "current_deal__services_end": None,
                }
            ),
        ]

        svc.refresh_companies()

        hubspot_api_client.get_companies.assert_called_once()

        company = db_session.query(HubSpotCompany).one()
        assert company.name == "COMPANY"
        assert company.hubspot_id == 100

    @pytest.mark.parametrize(
        "value,expected",
        [
            (None, None),
            ("2024-12-31", date(2024, 12, 31)),
            (datetime(2024, 12, 31).timestamp() * 1000, date(2024, 12, 31)),
        ],
    )
    def test_date_or_timestamp(self, expected, value):
        assert expected == date_or_timestamp(value)

    def test_factory(self, pyramid_request, db_session, HubSpotClient, HubSpot):
        svc = HubSpotService.factory(sentinel.context, pyramid_request)

        HubSpot.assert_called_once_with(access_token="HUBSPOT_API_KEY")
        HubSpotClient.assert_called_once_with(HubSpot.return_value)
        assert svc._db == db_session  # noqa: SLF001
        assert svc._region_code == "us"  # noqa: SLF001
        assert svc._client == HubSpotClient.return_value  # noqa: SLF001

    @pytest.fixture
    def HubSpotClient(self, patch):
        return patch("lms.services.hubspot.service.HubSpotClient")

    @pytest.fixture
    def HubSpot(self, patch):
        return patch("lms.services.hubspot.service.HubSpot")

    @pytest.fixture
    def hubspot_api_client(self):
        return create_autospec(HubSpotClient, spec_set=True, instance=True)

    @pytest.fixture
    def svc(self, db_session, hubspot_api_client):
        return HubSpotService(
            db=db_session, client=hubspot_api_client, region_code="us"
        )
