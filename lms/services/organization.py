from logging import getLogger
from typing import List, Optional

import sqlalchemy as sa
from sqlalchemy.orm import Session

from lms.models import ApplicationInstance, GroupInfo, Organization, Region
from lms.models.public_id import InvalidPublicId, PublicId

LOG = getLogger(__name__)


def _cast_to_int(value):
    try:
        if (int_value := int(value)) and int_value < 2147483647:
            return int_value

    except (ValueError, TypeError):
        return None


def _cast_to_public_id(string, region):
    try:
        return str(
            PublicId.parse(string, expect_model_code="org", expect_region=region)
        )
    except InvalidPublicId:
        return None


class OrganizationService:
    """A service for dealing with organization actions."""

    def __init__(self, db_session: Session):
        self._db_session = db_session

    def get_by_id(self, id_) -> Optional[Organization]:
        """Get an organization by its private primary key."""

        return self._organization_search_query(id_=id_).one_or_none()

    def get_by_public_id(self, public_id: str) -> Optional[List]:
        """Get an organization by its public_id."""

        return self._organization_search_query(public_id=public_id).one_or_none()

    # pylint:disable=too-many-arguments
    def search(
        self, id_=None, public_id=None, name=None, guid=None, limit=100
    ) -> List[Organization]:
        """
        Search for organizations.

        The results are returned as an OR of the specified filters.

        :param id_: Match on primary key
        :param public_id: Match on public id
        :param name: Match organization by name. Case-insensitive.
        :param guid: Match organizations linked in any way to the specified
            tool consumer instance GUID
        :param limit: Limit the number of results
        """
        return (
            self._organization_search_query(
                id_=id_, public_id=public_id, name=name, guid=guid
            )
            .limit(limit)
            .all()
        )

    def web_search(self, query, limit=100) -> List[Organization]:
        """Search for organizations based on a single query string."""

        # The trick here is we will attempt to search in every way we can
        # simultaneously, using the same query, as long as we can interpret it
        return self.search(
            id_=_cast_to_int(query),
            public_id=_cast_to_public_id(query, self._region),
            name=query,
            guid=query.strip(),
            limit=limit,
        )

    def _organization_search_query(
        self, id_=None, public_id=None, name=None, guid=None
    ):
        query = self._db_session.query(Organization)
        clauses = []

        if id_:
            clauses.append(Organization.id == id_)

        if public_id:
            clauses.append(Organization.public_id == public_id)

        if name:
            clauses.append(
                sa.func.to_tsvector("english", Organization.name).op("@@")(
                    sa.func.websearch_to_tsquery(name, postgresql_regconfig="english")
                )
            )

        if guid:
            query = query.outerjoin(ApplicationInstance).outerjoin(GroupInfo)

            clauses.extend(
                sa.or_(
                    ApplicationInstance.tool_consumer_instance_guid == guid,
                    GroupInfo.tool_consumer_instance_guid == guid,
                )
            )

        if clauses:
            query = query.filter(sa.or_(*clauses))

        return query

    def auto_assign_organization(
        self, application_instance: ApplicationInstance
    ) -> Optional[Organization]:
        """
        Automatically associate an application instance with an org by GUID.

        If there is no GUID matching is skipped, and we return `None`. If no
        match can be found, then a new organization is created.

        When more than one organization is found, the most recent will be used.
        """

        # We can't match by GUID if there isn't one
        guid = application_instance.tool_consumer_instance_guid
        if not guid:
            return None

        if application_instance.organization:
            org = application_instance.organization

        elif (
            orgs := self._organization_search_query(guid=guid)
            .order_by(Organization.updated.desc())
            .all()
        ):
            if len(orgs) > 1:
                LOG.warning(
                    "Multiple organization matches found for application instance %s",
                    application_instance.id,
                )

            org = orgs[0]

        else:
            org = self.create_organization()

        # Fill out missing names
        if not org.name and (name := application_instance.tool_consumer_instance_name):
            org.name = name

        application_instance.organization = org
        return org

    def create_organization(self, name=None) -> Organization:
        """Create new organizations."""
        org = Organization(name=name)
        self._db_session.add(org)
        # Ensure we have ids
        self._db_session.flush()

        return org

    def update_organization(self, organization, name=None, enabled=None):
        """Update an existing organization."""
        if name:
            organization.name = name

        if enabled is not None:
            organization.enabled = enabled

        return organization


def service_factory(_context, request) -> OrganizationService:
    """Get a new instance of OrganizationService."""

    return OrganizationService(db_session=request.db)
