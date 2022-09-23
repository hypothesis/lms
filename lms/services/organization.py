from logging import getLogger
from typing import List, Optional

import sqlalchemy as sa
from sqlalchemy.orm import Session

from lms.models import ApplicationInstance, GroupInfo, Organization

LOG = getLogger(__name__)


class OrganizationService:
    """A service for dealing with organization actions."""

    def __init__(self, db_session: Session):
        self._db_session = db_session

    def get_by_id(self, id_) -> Optional[Organization]:
        return self._db_session.query(Organization).filter_by(id=id_).one_or_none()

    def get_by_linked_guid(self, guid) -> List[Organization]:
        """Get organizations which match the provided GUID."""

        # There are huge numbers of null GUIDs, don't match on them
        if not guid:
            return []

        return (
            self._db_session.query(Organization)
            .join(ApplicationInstance)
            .outerjoin(GroupInfo)
            .filter(
                sa.or_(
                    ApplicationInstance.tool_consumer_instance_guid == guid,
                    GroupInfo.tool_consumer_instance_guid == guid,
                )
            )
            .order_by(Organization.updated.desc())
            .all()
        )

    def get_by_public_id(self, public_id: str) -> Optional[List]:
        """Get an organization by its public_id."""

        return self._search_query(public_id=public_id).one_or_none()

    def search(self, name, limit=100):
        """
        Search organizations.

        :param name: Match organization by name. Case-insensitive.
        :param limit: Limit the number of results
        """
        return self._search_query(name=name).limit(limit).all()

    def _search_query(self, public_id=None, name=None):
        clauses = []

        if public_id:
            clauses.append(Organization.public_id == public_id)

        if name:
            clauses.append(
                sa.func.to_tsvector("english", Organization.name).op("@@")(
                    sa.func.websearch_to_tsquery(name, postgresql_regconfig="english")
                )
            )

        query = self._db_session.query(Organization)
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

        elif orgs := self.get_by_linked_guid(guid):
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
