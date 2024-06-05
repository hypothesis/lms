import logging
from datetime import date, timedelta

from lms.services import HubSpotService, OrganizationUsageReportService
from lms.tasks.celery import app

LOG = logging.getLogger(__name__)


@app.task
def generate_usage_report(
    organization_id: int, tag: str, since: str, until: str
) -> None:
    with app.request_context() as request:
        with request.tm:
            request.find_service(OrganizationUsageReportService).generate_usage_report(
                organization_id,
                tag,
                date.fromisoformat(since),
                date.fromisoformat(until),
            )


@app.task
def schedule_monthly_deal_report(limit: int, backfill: int = 0) -> None:
    """Generate monthly usage reports for organizations with active deals.

    This task relies on being called from h-periodic a few times with the right limit value at the start of each month.

    backfill n reports in addition to the last month report.
    """
    reports_scheduled = 0

    with app.request_context() as request:
        with request.tm:
            usage_service = request.find_service(OrganizationUsageReportService)
            hubspot_service = request.find_service(HubSpotService)

            companies_with_active_deals = hubspot_service.get_companies_with_active_deals(
                # Get active deals, now and a few days ago to account for the last billing period
                date.today() - timedelta(days=30)
            )
            for company in companies_with_active_deals:
                organization = company.organization

                for since, until in usage_service.monthly_report_dates(
                    company.current_deal_services_start,
                    company.current_deal_services_end,
                    backfill + 1,
                ):
                    if usage_service.get(organization, "monthly-deal", since, until):
                        LOG.info(
                            "Report already exists %s:%s:%s",
                            organization.public_id,
                            since,
                            until,
                        )
                        return

                    generate_usage_report.delay(
                        organization.id,
                        "monthly-deal",
                        since.isoformat(),
                        until.isoformat(),
                    )

                    reports_scheduled += 1
                    if reports_scheduled >= limit:
                        # Limit the amount of reports we generate per call to this task
                        return
