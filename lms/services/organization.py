from dataclasses import dataclass
from datetime import datetime
from logging import getLogger

import sqlalchemy as sa
from sqlalchemy import Date, func, select
from sqlalchemy.orm import Session, aliased

from lms.db import full_text_match
from lms.models import (
    ApplicationInstance,
    GroupInfo,
    Grouping,
    GroupingMembership,
    Organization,
    User,
)
from lms.services.h_api import HAPI

LOG = getLogger(__name__)


@dataclass
class UsageReportRow:
    name: str | None
    email: str | None
    h_userid: str

    course_name: str
    course_created: datetime
    authority_provided_id: str


class InvalidOrganizationParent(Exception):
    """The requested Organization wasn't found or isn't an eligible parent."""


class OrganizationService:
    """A service for dealing with organization actions."""

    def __init__(self, db_session: Session, h_api: HAPI):
        self._db_session = db_session
        self._h_api = h_api

    def get_by_id(self, id_: int) -> Organization | None:
        """
        Get an organization by its private primary key.

        :param id_: Primary key of the organization
        """

        return self._organization_search_query(id_=id_).one_or_none()

    def get_by_public_id(self, public_id: str) -> list | None:
        """
        Get an organization by its public_id.

        :param public_id: Fully qualified public id
        """

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

        assert not hierarchy[-1].parent_id, "The root item should have no parent"

        return hierarchy[-1]

    def search(  # noqa: PLR0913
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
                "hypothesis", "auto_assigned_to_org", True
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
                org.settings.set("hypothesis", "auto_created", True)

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

    def update_organization(  # noqa: PLR0913
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

    def usage_report(
        self,
        organization: Organization,
        since: datetime,
        until: datetime,
    ):
        # Organizations that are children of the current one.
        # It includes the current org ID.
        organization_children = self.get_hierarchy_ids(
            organization.id, include_parents=False
        )
        # All the groups that can hold annotations (courses and segments) from this org
        groups_from_org = self._db_session.scalars(
            select(Grouping.authority_provided_id)
            .join(ApplicationInstance)
            .where(
                ApplicationInstance.organization_id.in_(organization_children),
                # If a group was created after the date we are interested, exclude it
                Grouping.created <= until,
            )
        ).all()

        if not groups_from_org:
            raise ValueError(f"No courses found for {organization.public_id}")

        # Of those groups, get the ones that do have annotations in the time period
        groups_with_annos = [
            group.authority_provided_id
            for group in self._h_api.get_groups(groups_from_org, since, until)
        ]
        if not groups_with_annos:
            raise ValueError(
                f"No courses with activity found for {organization.public_id}"
            )

        # Based on those groups generate the usage report based on the definition of unique user:
        # Users that belong to a course in which there are annotations in the time period
        parent = aliased(Grouping)
        query = (
            select(
                User.display_name.label("name"),
                User.email.label("email"),
                User.h_userid.label("h_userid"),
                Grouping.lms_name.label("course_name"),
                func.date_trunc("day", Grouping.created)
                .cast(Date)
                .label("course_created"),
                Grouping.authority_provided_id,
            )
            .select_from(User)
            .join(GroupingMembership)
            .join(Grouping)
            .distinct()
            .where(
                Grouping.authority_provided_id.in_(
                    # The report is based in courses so we query either
                    # groupings with no parent (courses) or the parents of segments (courses)
                    select(
                        func.coalesce(
                            parent.authority_provided_id, Grouping.authority_provided_id
                        )
                    )
                    .select_from(Grouping)
                    .outerjoin(parent, Grouping.parent_id == parent.id)
                    .where(Grouping.authority_provided_id.in_(groups_with_annos))
                ),
                # We can't exactly know the state of membership in the past but we can
                # know if someone was added to the group after the date we are interested
                GroupingMembership.created <= until,
            )
        )
        return [
            UsageReportRow(
                # Students might have name but they never have email
                name=row.name if row.email else "<STUDENT>",
                email=row.email if row.email else "<STUDENT>",
                h_userid=row.h_userid,
                course_name=row.course_name,
                course_created=row.course_created,
                authority_provided_id=row.authority_provided_id,
            )
            for row in self._db_session.execute(query).all()
        ]

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
        if parent.id in self.get_hierarchy_ids(organization.id, include_parents=False):
            raise InvalidOrganizationParent(
                f"Cannot use '{parent_public_id}' as a parent as it a "
                "child of this organization"
            )

        organization.parent = parent
        organization.parent_id = parent.id

    def get_hierarchy_ids(self, id_, include_parents=False) -> list[int]:
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
        rows = self._db_session.query(base_case.union(recursive_case)).all()  # type: ignore
        return [row[0] for row in rows]


def service_factory(_context, request) -> OrganizationService:
    """Get a new instance of OrganizationService."""

    return OrganizationService(
        db_session=request.db,
        h_api=request.find_service(HAPI),
    )
