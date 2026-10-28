from datetime import date, datetime
from unittest.mock import Mock, create_autospec, sentinel

import pytest

from lms.models import HubSpotCompany
from lms.services.hubspot import HubSpotService
from lms.services.hubspot._client import HubSpotClient
from lms.services.hubspot.service import date_or_timestamp, int_or_none
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
                    "current_deal__users_contracted": "1,500",
                    "student_fte": "17444",
                    "contract_type": "School",
                    # HubSpot IDs don't fit in a 32-bit integer
                    "hs_parent_company_id": "43892014728",
                }
            ),
            Mock(
                properties={
                    "lms_organization_id": "us.org.2",
                    "name": "NO DEAL",
                    "hs_object_id": 200,
                    "current_deal__services_start": None,
                    "current_deal__services_end": None,
                    "current_deal__users_contracted": None,
                    "student_fte": None,
                    # HubSpot sends empty properties as either None or ""
                    "contract_type": "",
                    "hs_parent_company_id": "",
                }
            ),
        ]

        svc.refresh_companies()

        hubspot_api_client.get_companies.assert_called_once()

        company, no_deal = db_session.query(HubSpotCompany).order_by(
            HubSpotCompany.hubspot_id
        )
        assert company.name == "COMPANY"
        assert company.hubspot_id == 100
        assert company.current_deal_users_contracted == 1500
        assert company.student_fte == 17444
        assert company.contract_type == "School"
        assert company.parent_hubspot_id == 43892014728
        assert no_deal.current_deal_users_contracted is None
        assert no_deal.student_fte is None
        assert no_deal.contract_type is None
        assert no_deal.parent_hubspot_id is None

    def test_export_companies_contract_billables(
        self, svc, hubspot_api_client, db_session
    ):
        organization = factories.Organization(public_id="TEST_ORG")
        company = factories.HubSpotCompany(
            lms_organization_id=organization.public_id,
            current_deal_services_start=date(2020, 1, 1),
            current_deal_services_end=date(2025, 1, 1),
        )
        # Two reports for the same org, we'd expect to get the numbers from the most recent one
        factories.OrganizationUsageReport(
            organization=organization,
            tag="test",
            key="test-older-report",
            until=date(2022, 1, 1),
            unique_users=10,
            unique_teachers=10,
        )
        factories.OrganizationUsageReport(
            organization=organization,
            tag="test",
            key="test-recent-report",
            until=date(2023, 1, 1),
            unique_users=100,
            unique_teachers=100,
        )
        db_session.flush()

        svc.export_companies_contract_billables(date(2024, 1, 1))

        hubspot_api_client.import_billables.assert_called_once_with(
            [(company.hubspot_id, 100, 100)], date_=date(2024, 1, 1)
        )

    @pytest.mark.parametrize(
        "value,expected",
        [
            (None, None),
            ("2024-12-31", date(2024, 12, 31)),
            (datetime(2024, 12, 31).timestamp() * 1000, date(2024, 12, 31)),  # noqa: DTZ001
        ],
    )
    def test_date_or_timestamp(self, expected, value):
        assert expected == date_or_timestamp(value)

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            # Absent: most companies have no current deal.
            (None, None),
            ("", None),
            # The ordinary case.
            ("1500", 1500),
            (1500, 1500),
            # HubSpot calls this a "formatted number", so it arrives
            # thousands-separated or with a decimal part even though a seat
            # count is whole.
            ("1,500", 1500),
            ("1500.0", 1500),
            ("1,500.00", 1500),
            # Unparseable values must not abort the refresh for every other
            # company in the batch.
            ("not a number", None),
            ("--", None),
        ],
    )
    def test_int_or_none(self, value, expected):
        assert int_or_none(value) == expected

    def test_factory(self, pyramid_request, db_session, HubSpotClient, HubSpot):
        svc = HubSpotService.factory(sentinel.context, pyramid_request)

        HubSpot.assert_called_once_with(access_token="HUBSPOT_API_KEY")  # noqa: S106
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
