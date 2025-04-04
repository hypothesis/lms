import base64
import uuid
from logging import getLogger

import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.orm import Session

from lms.db import full_text_match
from lms.models import (
    ApplicationInstance,
    Course,
    GroupInfo,
    GroupingMembership,
    Organization,
    User,
)

LOG = getLogger(__name__)


class InvalidOrganizationParent(Exception):  # noqa: N818
    """The requested Organization wasn't found or isn't an eligible parent."""


class InvalidPublicId(Exception):  # noqa: N818
    """Indicate an error with the specified public id."""


class OrganizationService:
    """A service for dealing with organization actions."""

    def __init__(self, db_session: Session, region_code: str):
        self._db_session = db_session
        self._region_code = region_code

    def get_by_id(self, id_: int) -> Organization | None:
        """
        Get an organization by its private primary key.

        :param id_: Primary key of the organization
        """

        return self._organization_search_query(id_=id_).one_or_none()

    def get_by_public_id(self, public_id: str) -> Organization | None:
        """
        Get an organization by its public_id.

        :param public_id: Fully qualified public id
        """
        parts = public_id.split(".")

        if not len(parts) == 4:
            raise InvalidPublicId(  # noqa: TRY003
                f"Malformed public id: '{public_id}'. Expected 4 dot separated parts."  # noqa: EM102
            )

        return self._organization_search_query(public_id=public_id).one_or_none()

    def get_hierarchy_root(self, id_: int) -> Organization:
        """
        Get the root of the hierarchy from the given organization.

        :param id_: Primary key of the organization
        """

        # Get all the objects in the hierarchy, to ensure they are cached by
        # SQLAlchemy, and should be fast to access.
        hierarchy = (
            self._db_session.query(Organization)
            .filter(
                Organization.id.in_(self.get_hierarchy_ids(id_, include_parents=True))
            )
            # Order by parent id, this will cause the root (if any) to be last.
            # The default ascending order puts NULL's last
            .order_by(Organization.parent_id)
        ).all()

        assert not hierarchy[-1].parent_id, "The root item should have no parent"  # noqa: S101

        return hierarchy[-1]

    def search(
        self, id_=None, public_id=None, name=None, guid=None, limit=100
    ) -> list[Organization]:
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
            clauses.append(full_text_match(Organization.name, name))

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
    ) -> Organization | None:
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
        else:
            # Add a note to indicate the application instance was automatically
            # allocated to an organization
            application_instance.settings.set(
                "hypothesis",
                "auto_assigned_to_org",
                True,  # noqa: FBT003
            )

            if (
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
                # Add a note to indicate the organization was automatically
                # created instead of going through our normal process
                org.settings.set("hypothesis", "auto_created", True)  # noqa: FBT003

        # Fill out missing names
        if not org.name and (name := application_instance.tool_consumer_instance_name):
            org.name = name

        application_instance.organization = org

        return org

    def create_organization(self, name=None) -> Organization:
        """Create new organizations."""
        org = Organization(name=name, public_id=self._generate_public_id())
        self._db_session.add(org)
        # Ensure we have ids
        self._db_session.flush()

        return org

    def _generate_public_id(self):
        # We don't use a standard UUID-4 format here as they are common in Tool
        # Consumer Instance GUIDs, and might be confused for them. These also
        # happen to be shorter and guaranteed URL safe.
        id_ = base64.urlsafe_b64encode(uuid.uuid4().bytes).decode("ascii").rstrip("=")

        # We use '.' as the separator here because it's not in base64, but it
        # is URL safe. The other option is '~'.
        return f"{self._region_code}.lms.org.{id_}"

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
            raise InvalidOrganizationParent(  # noqa: TRY003
                "Cannot set an organization to be it's own parent"  # noqa: EM101
            )

        parent = self._organization_search_query(
            public_id=parent_public_id
        ).one_or_none()
        if not parent:
            raise InvalidOrganizationParent(  # noqa: TRY003
                f"Could not find parent organization: '{parent_public_id}'"  # noqa: EM102
            )

        # Get a list including our self and all are children etc.
        if parent.id in self.get_hierarchy_ids(organization.id, include_parents=False):
            raise InvalidOrganizationParent(  # noqa: TRY003
                f"Cannot use '{parent_public_id}' as a parent as it a "  # noqa: EM102
                "child of this organization"
            )

        organization.parent = parent
        organization.parent_id = parent.id

    def get_hierarchy_ids(self, id_, include_parents=False) -> list[int]:  # noqa: FBT002
        """
        Get an organization and it's children's ids order not guaranteed.

        :param id_: Organization id to look for
        :param include_parents: Include parents as well as children
        """

        # Find the relevant orgs in the hierarchy by id using a recursive CTE:
        # https://www.postgresql.org/docs/current/queries-with.html#QUERIES-WITH-RECURSIVE
        cols = [Organization.id, Organization.parent_id]
        base_case = (
            self._db_session.query(*cols)
            .filter(Organization.id == id_)
            # The name of the CTE is arbitrary, but must be present
            .cte("organizations", recursive=True)
        )

        # We are going to self join onto the above with anything that is a
        # child of the objects we've seen so far
        join_condition = Organization.parent_id == base_case.c.id
        if include_parents:
            # Match anything that is a parent of what we've seen
            join_condition = sa.or_(
                join_condition, Organization.id == base_case.c.parent_id
            )

        recursive_case = self._db_session.query(*cols).join(base_case, join_condition)

        # This will recurse until no new rows are added
        rows = self._db_session.query(base_case.union(recursive_case)).all()  # type: ignore  # noqa: PGH003
        return [row[0] for row in rows]

    def is_member(self, organization: Organization, user: User) -> bool:
        """
        Check if user is a member organization.

        We define "member" here as belonging to any of the organization's courses.
        """
        query = (
            select(GroupingMembership)
            .join(Course)
            .join(ApplicationInstance)
            .where(
                GroupingMembership.user_id == user.id,
                ApplicationInstance.organization_id == organization.id,
            )
            .limit(1)
        )
        return bool(self._db_session.execute(query).scalar())


def service_factory(_context, request) -> OrganizationService:
    """Get a new instance of OrganizationService."""

    return OrganizationService(
        db_session=request.db,
        region_code=request.registry.settings["region_code"],
    )
