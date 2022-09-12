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
            org = Organization()

        # Fill out missing names
        if not org.name and (name := application_instance.tool_consumer_instance_name):
            org.name = name

        application_instance.organization = org
        return org


def service_factory(_context, request) -> OrganizationService:
    """Get a new instance of OrganizationService."""

    return OrganizationService(db_session=request.db)
