from dataclasses import dataclass, field
from typing import List

from lms.db import full_text_match, BASE
from lms.models import ApplicationInstance, LTIRegistration, JSONSettings, \
    Organization

import sqlalchemy as sa
from sqlalchemy.orm import Query, Session

from tests import factories


def email_or_domain_match(*fields):
    def email_or_domain_match(value):
        return sa.or_(
            sa.func.lower(field) == value.lower()
            if "@" in value
            else field.ilike(f"%@{value}")
            for field in fields
        )

    return email_or_domain_match

# Filter classes ---------------

@dataclass
class SearchFilter:
    model: BASE
    """The model in question, used for basic attribute lookups."""

    filters: dict = field(default_factory=dict)
    """A dict of names to functions for providing query filters."""

    key_map: dict = field(
        default_factory=lambda: {"id_": "id", "type_": "type"})
    """A mapping from kwarg names to parameters / filter names."""

    def get_clauses(self, kwargs):
        # If we name spaced things, we wouldn't have to do this popping
        # business to prevent following filters from grabbing things.
        # We could even use this behavior explicitly as a way of querying all
        # relevant objects for the given value. For example, search everything
        # which supports "email" and then return the result as an OR. Or
        # perhaps "*.email" to be explicit.
        to_pop = []

        for key, value in kwargs.items():
            if value is None:
                continue

            # Avoid reserved names like 'id'
            key = self.key_map.get(key, key)

            # We have a dedicated function to provide a clause
            if filter_function := self.filters.get(key):
                to_pop.append(key)
                yield filter_function(value)

            # This is a plain lookup on the model by attribute
            elif hasattr(self.model, key):
                to_pop.append(key)
                yield getattr(self.model, key) == value

        # Hmm.... :<
        for key in to_pop:
            kwargs.pop(key)


@dataclass
class FilterChain:
    search_filters: List[SearchFilter]

    def search(self, db_session: Session, kwargs, combine=sa.and_) -> Query:
        query = None
        clauses = []

        for search_filter in self.search_filters:
            new_clauses = list(search_filter.get_clauses(kwargs))
            clauses.extend(new_clauses)

            if query is None:
                query = db_session.query(search_filter.model)
            elif new_clauses:
                query = query.outerjoin(search_filter.model)

        return query.filter(combine(*clauses))

# Filter -----------------------

LTI_REG_FILTER = SearchFilter(LTIRegistration)

ORG_FILTER = SearchFilter(Organization, filters={
    "name": lambda value: full_text_match(Organization.name, value),
})

AI_FILTER = SearchFilter(
    ApplicationInstance,
    filters={
        "name": lambda value: full_text_match(ApplicationInstance.name, value),
        "settings": lambda value: JSONSettings.matching(
            ApplicationInstance.settings, value
        ),
        "email": email_or_domain_match(
            ApplicationInstance.requesters_email,
            ApplicationInstance.tool_consumer_instance_contact_email,
        ),
        "guid": lambda value: sa.or_(
            ApplicationInstance.tool_consumer_instance_guid == value,
            ApplicationInstance.group_infos.any(tool_consumer_instance_guid=value)
        )
    },
)

AI_SEARCH = FilterChain([AI_FILTER, LTI_REG_FILTER, ORG_FILTER])
REG_SEARCH = FilterChain([LTI_REG_FILTER])
ORG_SEARCH = FilterChain([ORG_FILTER, AI_FILTER])

# Search -----------------------

def search_for_ais(db_session, kwargs):
    return AI_SEARCH.search(db_session, kwargs).all()

def search_for_lti_registrations(db_session, kwargs):
    return REG_SEARCH.search(db_session, kwargs).all()

def search_for_orgs(db_session, kwargs):
    return ORG_SEARCH.search(db_session, kwargs, combine=sa.or_).all()


class TestWoo:
    def test_it(self, db_session):
        org = factories.Organization.create(name='org_name')
        lti_reg = factories.LTIRegistration.create(issuer="my_issuer")
        ai = factories.ApplicationInstance(name="ai_name", organization=org, lti_registration=lti_reg)
        factories.GroupInfo(tool_consumer_instance_guid="gi_guid", application_instance=ai)
        db_session.flush()

        items = search_for_ais(db_session, {"guid": "gi_guid"})

        assert items == [ai]

    def test_it2(self, db_session):
        org = factories.Organization.create(name='org_name')
        org_2 = factories.Organization.create(name='org_name_2')
        lti_reg = factories.LTIRegistration.create(issuer="my_issuer")
        ai = factories.ApplicationInstance(name="ai_name", organization=org, lti_registration=lti_reg)
        factories.GroupInfo(tool_consumer_instance_guid="gi_guid", application_instance=ai)
        db_session.flush()

        items = search_for_orgs(db_session, {"guid": "gi_guid", "name": "org_name_2"})

        assert items == [org, org_2]

    def test_it3(self, db_session):
        org = factories.Organization.create(name='org_name')
        lti_reg = factories.LTIRegistration.create(issuer="my_issuer")
        ai = factories.ApplicationInstance(
            name="ai_name", organization=org, lti_registration=lti_reg,
            requesters_email="foo@example.com"
        )
        factories.GroupInfo(tool_consumer_instance_guid="gi_guid", application_instance=ai)
        db_session.flush()

        items = search_for_orgs(db_session, {"email": "foo@example.com"})

        assert items == [org]