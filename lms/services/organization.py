from logging import getLogger
from typing import List, Optional

import sqlalchemy as sa
from sqlalchemy.orm import Session

from lms.models import ApplicationInstance, GroupInfo, Organization
from lms.validation import ValidationError

LOG = getLogger(__name__)


class OrganizationService:
    """A service for dealing with organization actions."""

    def __init__(self, db_session: Session, region):
        self._db_session = db_session
        self._region = region

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

    def get_by_public_id(self, public_id: str):
        try:
            region_code, app, type_, public_id = public_id.split(".")
        except ValueError as err:
            raise ValidationError(
                messages={"public_id": [f"{public_id} doesn't have the right format"]}
            ) from err

        if region_code != self._region.code:
            raise ValidationError(
                messages={
                    "public_id": [
                        f"{region_code} doesn't match current region: {self._region.code}"
                    ]
                }
            )

        if app != "lms":
            raise ValidationError(
                messages={"public_id": [f"{app} doesn't match app region: lms"]}
            )

        if type_ != "org":
            raise ValidationError(
                messages={
                    "public_id": [f"{type_} doesn't match organization type: 'org'"]
                }
            )

        return (
            self._db_session.query(Organization)
            .filter_by(_public_id=public_id)
            .one_or_none()
        )

    def update_organization(self, organization: Organization, **kwargs):
        for field in ["name", "enabled"]:
            current_value = getattr(organization, field)
            update_value = kwargs[field]
            # Don't set any values if they match the ones in the object.
            # Otherwise the session is marked as dirty making difficult to track
            # changes and the `updated` field keeps getting a new value despite not
            # having any new values.
            if current_value != update_value:
                setattr(organization, field, update_value)

        return organization

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
            self._db_session.add(org)
            # Ensure we have ids
            self._db_session.flush()

        # Fill out missing names
        if not org.name and (name := application_instance.tool_consumer_instance_name):
            org.name = name

        application_instance.organization = org
        return org


def service_factory(_context, request) -> OrganizationService:
    """Get a new instance of OrganizationService."""

    return OrganizationService(db_session=request.db, region=request.region)
