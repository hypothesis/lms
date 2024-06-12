from contextlib import contextmanager
from datetime import date
from unittest.mock import sentinel

import pytest
from freezegun import freeze_time

from lms.tasks.organization import generate_usage_report, schedule_monthly_deal_report
from tests import factories


class TestGenerateUsageReport:
    def test_generate_usage_report(self, organization_usage_report_service):
        generate_usage_report(sentinel.id, sentinel.tag, "2024-01-01", "2024-02-02")

        organization_usage_report_service.generate_usage_report.assert_called_once_with(
            sentinel.id, sentinel.tag, date(2024, 1, 1), date(2024, 2, 2)
        )


class TestScheduleMonthlyDealReport:
    @freeze_time("2023-03-09 05:15:00")
    def test_schedule_monthly_deal_report(
        self, organization_usage_report_service, hubspot_service, generate_usage_report
    ):
        organization = factories.Organization()
        hubspot_service.get_companies_with_active_deals.return_value = [
            factories.HubSpotCompany(
                organization=organization,
                lms_organization_id=organization.public_id,
                current_deal_services_start=date(2022, 1, 1),
                current_deal_services_end=date(2022, 12, 31),
            )
        ]
        organization_usage_report_service.get.return_value = None
        organization_usage_report_service.monthly_report_dates.return_value = [
            (date(2022, 1, 1), date(2023, 2, 28))
        ]

        schedule_monthly_deal_report(limit=10)
        hubspot_service.get_companies_with_active_deals.assert_called_once_with(
            date(2023, 2, 7)
        )

        generate_usage_report.delay.assert_called_once_with(
            organization.id, "monthly-deal", "2022-01-01", "2023-02-28"
        )

    @freeze_time("2023-03-09 05:15:00")
    def test_schedule_monthly_deal_report_existing_report(
        self, organization_usage_report_service, hubspot_service, generate_usage_report
    ):
        organization = factories.Organization()
        hubspot_service.get_companies_with_active_deals.return_value = [
            factories.HubSpotCompany(
                organization=organization,
                lms_organization_id=organization.public_id,
                current_deal_services_start=date(2022, 1, 1),
                current_deal_services_end=date(2022, 12, 31),
            )
        ]
        organization_usage_report_service.monthly_report_dates.return_value = [
            (date(2022, 1, 1), date(2023, 2, 28))
        ]
        organization_usage_report_service.get.return_value = (
            factories.OrganizationUsageReport()
        )

        schedule_monthly_deal_report(limit=1)

        hubspot_service.get_companies_with_active_deals.assert_called_once_with(
            date(2023, 2, 7)
        )

        generate_usage_report.delay.assert_not_called()

    @freeze_time("2023-03-09 05:15:00")
    def test_schedule_monthly_deal_report_limit(
        self, organization_usage_report_service, hubspot_service, generate_usage_report
    ):
        organization = factories.Organization()
        hubspot_service.get_companies_with_active_deals.return_value = [
            factories.HubSpotCompany(
                organization=organization,
                lms_organization_id=organization.public_id,
                current_deal_services_start=date(2022, 1, 1),
                current_deal_services_end=date(2022, 12, 31),
            ),
            factories.HubSpotCompany(
                organization=organization,
                lms_organization_id=organization.public_id,
                current_deal_services_start=date(2022, 1, 1),
                current_deal_services_end=date(2022, 12, 31),
            ),
        ]
        organization_usage_report_service.get.side_effect = [
            factories.OrganizationUsageReport(),  # First report already exists, it should not have an effect on limit
            None,  # Second needs to be generated, limit will stop here
            None,  # Third won't be generated
        ]
        organization_usage_report_service.monthly_report_dates.return_value = [
            (date(2022, 1, 1), date(2022, 12, 31)),
            (date(2022, 1, 1), date(2022, 11, 30)),
            (date(2022, 1, 1), date(2022, 10, 31)),
        ]

        schedule_monthly_deal_report(limit=1)

        generate_usage_report.delay.assert_called_once()

    @pytest.fixture
    def generate_usage_report(self, patch):
        return patch("lms.tasks.organization.generate_usage_report")


@pytest.fixture(autouse=True)
def app(patch, pyramid_request):
    app = patch("lms.tasks.organization.app")

    @contextmanager
    def request_context():
        yield pyramid_request

    app.request_context = request_context

    return app
