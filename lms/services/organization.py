from logging import getLogger
from typing import List, Optional

import sqlalchemy as sa
from sqlalchemy.orm import Session

from lms.models import ApplicationInstance, GroupInfo, Organization

LOG = getLogger(__name__)


class InvalidOrganizationParent(Exception):
    """The requested Organization wasn't found or isn't an eligible parent."""


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
                    sa.func.websearch_to_tsquery("english", name)
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

    def update_organization(
        self,
        organization: Organization,
        name=None,
        enabled=None,
        notes=None,
        parent_public_id=...,
    ) -> Organization:
        """
        Update an existing organization.

        :param organization: Organization to update
        :param name: Set the name (if not `None`)
        :param enabled: Enable or disable (if not `None`)
        :param notes: Set notes (if not `None`)
        :param parent_public_id: Set or remove the parent (if set at all)

        :raises InvalidOrganizationParent: If the parent cannot be found or
            isn't a valid organization for one reason or another.
        """

        if name:
            organization.name = name

        if enabled is not None:
            organization.enabled = enabled

        if notes is not None:
            organization.settings.set("hypothesis", "notes", notes)

        # Use the fact the default is ... to allow us to blank or set based on
        # the param being present
        if parent_public_id is None:
            organization.parent = None
            organization.parent_id = None
        elif parent_public_id is not ...:
            self._move_organization_parent(organization, parent_public_id)

        return organization

    def _move_organization_parent(self, organization: Organization, parent_public_id):
        """Change an organizations parent, without creating loops."""

        # This would be caught by the next check, but doing it here means we
        # can give a more sensible error message
        if parent_public_id == organization.public_id:
            raise InvalidOrganizationParent(
                "Cannot set an organization to be it's own parent"
            )

        parent = self._organization_search_query(
            public_id=parent_public_id
        ).one_or_none()
        if not parent:
            raise InvalidOrganizationParent(
                f"Could not find parent organization: '{parent_public_id}'"
            )

        # Get a list including our self and all are children etc.
        if parent.id in self._get_hierarchy_ids(organization.id):
            raise InvalidOrganizationParent(
                f"Cannot use '{parent_public_id}' as a parent as it a "
                "child of this organization"
            )

        organization.parent = parent
        organization.parent_id = parent.id

    def _get_hierarchy_ids(self, id_) -> List[int]:
        """
        Get an organization and it's children's ids order not guaranteed.

        :param id_: Organization id to look for
        """

        # Find the relevant orgs in the hierarchy by id using a recursive CTE:
        # https://www.postgresql.org/docs/current/queries-with.html#QUERIES-WITH-RECURSIVE
        cols = [Organization.id, Organization.parent_id]
        base_case = (
            self._db_session.query(*cols).filter(Organization.id == id_)
            # The name of the CTE is arbitrary, but must be present
            .cte("organizations", recursive=True)
        )

        # We are going to self join onto the above with anything that is a
        # child of the objects we've seen so far
        join_condition = Organization.parent_id == base_case.c.id
        recursive_case = self._db_session.query(*cols).join(base_case, join_condition)

        # This will recurse until no new rows are added
        rows = self._db_session.query(base_case.union(recursive_case)).all()
        return [row[0] for row in rows]


def service_factory(_context, request) -> OrganizationService:
    """Get a new instance of OrganizationService."""

    return OrganizationService(db_session=request.db)
