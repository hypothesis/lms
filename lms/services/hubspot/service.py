from datetime import date, datetime

from hubspot import HubSpot
from sqlalchemy import func, select
from sqlalchemy.exc import MultipleResultsFound

from lms.models import HubSpotCompany, Organization, OrganizationUsageReport
from lms.services.hubspot._client import HubSpotClient
from lms.services.upsert import bulk_upsert


class HubSpotService:
    def __init__(self, db, client: HubSpotClient, region_code: str):
        self._db = db
        self._client = client
        self._region_code = region_code

    def get_company(self, organization_id: str) -> HubSpotCompany | None:
        """Get the HubSpot company associated to the given LMS organization ID."""
        try:
            return self._db.scalars(
                select(HubSpotCompany).where(
                    HubSpotCompany.lms_organization_id == organization_id
                )
            ).one_or_none()
        except MultipleResultsFound:
            # More than one company pointing to the same org is a data entry error, ignore them.
            return None

    def _companies_with_active_deals_query(self, date_: date):
        # Exclude companies that map to the same Organization.
        # We allow these on the DB to be able to report on the situation to prompt a human to fix it.
        non_duplicated_companies = (
            select(HubSpotCompany.lms_organization_id)
            .group_by(HubSpotCompany.lms_organization_id)
            .having(func.count(HubSpotCompany.lms_organization_id) == 1)
        )
        return select(HubSpotCompany).where(
            # Exclude duplicates
            HubSpotCompany.lms_organization_id.in_(non_duplicated_companies),
            # Only companies with a link to an organization
            HubSpotCompany.organization != None,  # noqa: E711
            HubSpotCompany.current_deal_services_start <= date_,
            HubSpotCompany.current_deal_services_end >= date_,
        )

    def get_companies_with_active_deals(self, date_: date) -> list[HubSpotCompany]:
        """Get all HubSpotCompany that have active deals in `date`."""
        return self._db.scalars(self._companies_with_active_deals_query(date_)).all()

    def refresh_companies(self) -> None:
        """Refresh all companies in the DB upserting accordingly."""
        companies = self._client.get_companies()

        bulk_upsert(
            self._db,
            HubSpotCompany,
            [
                {
                    "hubspot_id": int(company.properties["hs_object_id"]),
                    "name": company.properties["name"],
                    "lms_organization_id": company.properties["lms_organization_id"],
                    "current_deal_services_start": date_or_timestamp(
                        company.properties["current_deal__services_start"]
                    ),
                    "current_deal_services_end": date_or_timestamp(
                        company.properties["current_deal__services_end"]
                    ),
                }
                for company in companies
                # Only get companies with an org ID
                if company.properties["lms_organization_id"]
                # only for the current region
                and company.properties["lms_organization_id"].startswith(
                    self._region_code
                )
            ],
            index_elements=["hubspot_id"],
            update_columns=[
                "name",
                "lms_organization_id",
                "current_deal_services_start",
                "current_deal_services_end",
            ],
        )

    def export_companies_contract_billables(self, date_: date):
        """Export the contract billable numbers to HubSpot."""
        query = (
            self._companies_with_active_deals_query(date_)
            .join(
                Organization,
                Organization.public_id == HubSpotCompany.lms_organization_id,
            )
            .join(OrganizationUsageReport)
            .distinct(OrganizationUsageReport.organization_id)
            .order_by(
                OrganizationUsageReport.organization_id,
                OrganizationUsageReport.until.desc(),
            )
        ).with_only_columns(
            HubSpotCompany.hubspot_id,
            OrganizationUsageReport.unique_teachers,
            OrganizationUsageReport.unique_users,
        )

        # From the point of view of HubSpot we are creating an import
        self._client.import_billables(self._db.execute(query).all(), date_=date_)

    @classmethod
    def factory(cls, _context, request):
        return cls(
            db=request.db,
            client=HubSpotClient(
                HubSpot(access_token=request.registry.settings["hubspot_api_key"])
            ),
            region_code=request.registry.settings["region_code"],
        )


def date_or_timestamp(value: str | int | None) -> date | None:
    """
    Format either timestamp or already formatted dates as YYYY-MM-DD.

    We seem to be getting different formats for the same fields,
    coerce them to always be string formated dates.
    """
    if not value:
        return None
    try:
        return date.fromtimestamp(int(value) / 1000)
    except ValueError:
        # Date is already formatted, return it as a date object
        return datetime.strptime(str(value), "%Y-%m-%d").date()
