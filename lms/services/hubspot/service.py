from datetime import datetime

from hubspot import HubSpot
from sqlalchemy import select
from sqlalchemy.exc import MultipleResultsFound

from lms.models.hubspot import HubSpotCompany
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

    @classmethod
    def factory(cls, _context, request):
        return cls(
            db=request.db,
            client=HubSpotClient(
                HubSpot(access_token=request.registry.settings["hubspot_api_key"])
            ),
            region_code=request.registry.settings["region_code"],
        )


def date_or_timestamp(value: str | int | None) -> str | None:
    """
    Format either timestamp or already formatted dates as YYYY-MM-DD.

    We seem to be getting different formats for the same fields,
    coerce them to always be string formated dates.
    """
    if not value:
        return None
    try:
        return datetime.fromtimestamp(int(value) / 1000).strftime("%Y-%m-%d")
    except ValueError:
        # Date is already formatted, return it verbatim
        return value
