import os
from lms.services.hubspot import HubspotClient
from dataclasses import dataclass

from typing import Callable, Generator, Iterable, List, Optional, Set
from datetime import datetime


def date_or_timestamp(value):
    """
    Format either timestamp or already formatted dates as YYYY-MM-DD.

    We seem to be getting different formats for the same fields,
    coerce them to always be string formated dates.
    """
    try:
        return datetime.fromtimestamp(int(value) / 1000).strftime("%Y-%m-%d")
    except ValueError:
        # Date is already formatted, return it verbatim
        return value


@dataclass
class Field:
    """Define a mapping from a remote field to a chosen key."""

    hs_field: str
    key: str | None = None
    mapping: Callable | None = None

    def __post_init__(self):
        if not self.key:
            self.key = self.hs_field


COMPANY_FIELDS = (
    Field("hs_object_id", "id", mapping=int),
    Field("name", mapping=str),
    Field("lms_organization_id", mapping=str),
    Field("lifecyclestage", "life_cycle_stage", mapping=str),
    # Owners
    Field("hubspot_owner_id", "company_owner_id", mapping=int),
    Field("owner__success", "success_owner_id", mapping=int),
    # Cohort
    Field(
        "cohort__pilot_first_date", "cohort_pilot_first_date", mapping=date_or_timestamp
    ),
    Field(
        "cohort__subscription_first_date",
        "cohort_subscription_first_date",
        mapping=date_or_timestamp,
    ),
    # Deals
    Field("current_deal__services_start", "current_deal_services_start"),
    Field("current_deal__services_end", "current_deal_services_end"),
    Field("current_deal__amount", "current_deal_amount", mapping=float),
    Field(
        "current_deal__users_contracted", "current_deal_users_contracted", mapping=int
    ),
)


def test_it():
    api_client = HubspotClient(private_app_key=os.environ["HUBSPOT_API_KEY"])
    companies = list(api_client.get_companies(COMPANY_FIELDS))

    print(companies)
