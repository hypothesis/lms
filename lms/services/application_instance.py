import secrets
from datetime import datetime
from functools import lru_cache
from logging import getLogger

import sqlalchemy as sa
from sqlalchemy.exc import NoResultFound

from lms.db import full_text_match
from lms.models import ApplicationInstance, JSONSettings, LTIParams, LTIRegistration
from lms.services.aes import AESService
from lms.services.exceptions import SerializableError
from lms.services.organization import OrganizationService
from lms.validation import ValidationError

LOG = getLogger(__name__)


class ApplicationInstanceNotFound(Exception):
    """The requested ApplicationInstance wasn't found in the database."""


class AccountDisabled(SerializableError):
    """Indicate that we have disabled this account through it's org."""

    def __init__(self, application_instance: ApplicationInstance):
        super().__init__(
            message="Account has been disabled",
            error_code="account_disabled",
            details={
                "organization_id": application_instance.organization.public_id,
                "application_instance_id": application_instance.id,
            },
        )


class ProvisioningDisabled(SerializableError):
    """
    Indicate that provisioning is not enabled for this instance.

    We suspect this is not actually in use.
    Revisit after a while to completely remove the notion of "provisioning"
    """

    def __init__(self, application_instance: ApplicationInstance):
        super().__init__(
            message="User and group provisioning not enabled for instance",
            error_code="instance_provisioning",
            details={
                "application_instance_id": application_instance.id,
            },
        )


def _email_or_domain_match(columns, email):
    """
    Get an SQL comparator for matching emails.

    This will match the full email if it contains '@' or interpret the text
    as a domain if not. This will search over all the provided fields.
    """
    return sa.or_(
        (
            sa.func.lower(column) == email.lower()
            if "@" in email
            else column.ilike(f"%@{email}")
        )
        for column in columns
    )


class ApplicationInstanceService:
    def __init__(
        self,
        db,
        aes_service: AESService,
        organization_service: OrganizationService,
    ):
        self._db = db
        self._aes_service = aes_service
        self._organization_service = organization_service

    @lru_cache(maxsize=1)
    def get_for_launch(self, id_) -> ApplicationInstance:
        """
        Return the current request's `ApplicationInstance`.

        This is the `ApplicationInstance` with `id` matching
        `request.application_instance_id`.

        :raises ApplicationInstanceNotFound: if there's no matching
            `ApplicationInstance`
        :raise AccountDisabled: If the organization associated with this
            instance is disabled
        :raise ProvisioningDisabled: if the instance has provisioning
            disabled
        """
        if id_:
            application_instance = self.get_by_id(id_)

            # Check to see if this application instance belongs to a disabled
            # organization.
            if (
                application_instance
                and (org := application_instance.organization)
                and not org.enabled
            ):
                LOG.info(
                    "Account access was blocked for application_instance=%s org=%s",
                    application_instance.id,
                    org.id,
                )
                raise AccountDisabled(application_instance)

            if application_instance and not application_instance.provisioning:
                raise ProvisioningDisabled(application_instance)

            return application_instance

        raise ApplicationInstanceNotFound()

    @lru_cache(maxsize=1)
    def get_by_id(self, id_) -> ApplicationInstance:
        try:
            return self._ai_search_query(id_=id_).one()
        except NoResultFound as err:
            raise ApplicationInstanceNotFound() from err

    @lru_cache(maxsize=128)
    def get_by_consumer_key(self, consumer_key) -> ApplicationInstance:
        """
        Return the `ApplicationInstance` with the given `consumer_key`.

        :param consumer_key: Consumer key to search by
        :raise ApplicationInstanceNotFound: if there's no matching
            `ApplicationInstance`
        """
        if not consumer_key:
            raise ApplicationInstanceNotFound()

        try:
            return self._ai_search_query(consumer_key=consumer_key).one()
        except NoResultFound as err:
            raise ApplicationInstanceNotFound() from err

    @lru_cache(maxsize=128)
    def get_by_deployment_id(
        self, issuer: str, client_id: str, deployment_id: str
    ) -> ApplicationInstance:
        if not all([issuer, client_id, deployment_id]):
            raise ApplicationInstanceNotFound()

        try:
            return self._ai_search_query(
                issuer=issuer, client_id=client_id, deployment_id=deployment_id
            ).one()

        except NoResultFound as err:
            raise ApplicationInstanceNotFound() from err

    def search(  # noqa: PLR0913
        self,
        *,
        id_=None,
        name=None,
        consumer_key=None,
        issuer=None,
        client_id=None,
        deployment_id=None,
        tool_consumer_instance_guid=None,
        limit=100,
        email=None,
        settings=None,
        organization_public_id=None,
    ) -> list[ApplicationInstance]:
        """Return the instances that match all of the passed parameters."""

        return (
            self._ai_search_query(
                id_=id_,
                name=name,
                consumer_key=consumer_key,
                issuer=issuer,
                client_id=client_id,
                deployment_id=deployment_id,
                tool_consumer_instance_guid=tool_consumer_instance_guid,
                email=email,
                settings=settings,
                organization_public_id=organization_public_id,
            )
            .order_by(
                ApplicationInstance.last_launched.desc().nulls_last(),
                ApplicationInstance.updated.desc(),
            )
            .limit(limit)
            .all()
        )

    # pylint: disable=too-complex
    def _ai_search_query(  # noqa: C901, PLR0913
        self,
        *,
        id_=None,
        name=None,
        consumer_key=None,
        issuer=None,
        client_id=None,
        deployment_id=None,
        tool_consumer_instance_guid=None,
        email=None,
        settings=None,
        organization_public_id=None,
    ):
        """Return a query with the passed parameters applied as filters."""

        query = self._db.query(ApplicationInstance).outerjoin(LTIRegistration)
        if id_:
            query = query.filter(ApplicationInstance.id == id_)

        if name:
            query = query.filter(full_text_match(ApplicationInstance.name, name))

        if consumer_key:
            query = query.filter(ApplicationInstance.consumer_key == consumer_key)

        if issuer:
            query = query.filter_by(issuer=issuer)

        if client_id:
            query = query.filter_by(client_id=client_id)

        if deployment_id:
            query = query.filter(ApplicationInstance.deployment_id == deployment_id)

        if tool_consumer_instance_guid:
            query = query.filter(
                ApplicationInstance.tool_consumer_instance_guid
                == tool_consumer_instance_guid
            )

        if email:
            query = query.filter(
                _email_or_domain_match(
                    (
                        ApplicationInstance.requesters_email,
                        ApplicationInstance.tool_consumer_instance_contact_email,
                    ),
                    email,
                )
            )

        if settings:
            query = query.filter(
                JSONSettings.matching(ApplicationInstance.settings, settings)
            )

        if organization_public_id:
            query = query.filter(
                ApplicationInstance.organization.has(public_id=organization_public_id)
            )

        return query

    def update_application_instance(  # noqa: PLR0913, PLR0917
        self,
        application_instance,
        name=None,
        lms_url=None,
        deployment_id=None,
        developer_key=None,
        developer_secret=None,
        organization_public_id=None,
    ):
        if name:
            application_instance.name = name

        if lms_url:
            application_instance.lms_url = lms_url

        if deployment_id:
            application_instance.deployment_id = deployment_id

        if developer_key:
            application_instance.developer_key = developer_key

        if developer_secret:
            aes_iv = self._aes_service.build_iv()
            encrypted_secret = self._aes_service.encrypt(aes_iv, developer_secret)
            application_instance.aes_cipher_iv = aes_iv
            application_instance.developer_secret = encrypted_secret

        if organization_public_id:
            org = self._organization_service.get_by_public_id(organization_public_id)
            if org:
                application_instance.organization = org
            else:
                raise ValidationError(
                    messages={
                        "organization_public_id": [
                            f"Organization {organization_public_id} not found"
                        ]
                    }
                )

    def create_application_instance(  # noqa: PLR0913, PLR0917
        self,
        lms_url,
        email,
        developer_key,
        developer_secret,
        organization_public_id,
        name,
        deployment_id=None,
        lti_registration_id=None,
    ) -> ApplicationInstance:
        """Create an application instance."""
        consumer_key = (
            "Hypothesis" + secrets.token_hex(16) if not deployment_id else None
        )

        application_instance = ApplicationInstance(
            name=name,
            consumer_key=consumer_key,
            shared_secret=secrets.token_hex(32),
            lms_url=lms_url,
            requesters_email=email,
            created=datetime.utcnow(),
            # Some helpful defaults for settings
            settings={
                "canvas": {
                    "sections_enabled": False,
                    "groups_enabled": bool(developer_key),
                    "files_enabled": bool(developer_key),
                },
                "google_drive": {"files_enabled": True},
                "hypothesis": {"instructor_email_digests_enabled": True},
            },
            deployment_id=deployment_id,
            lti_registration_id=lti_registration_id,
        )
        # If either one of developer_key or developer_secret is missing,
        # then we won't set either on creation
        if not all([developer_secret, developer_key]):
            developer_key = developer_secret = None

        self.update_application_instance(
            application_instance,
            developer_key=developer_key,
            developer_secret=developer_secret,
            organization_public_id=organization_public_id,
        )
        self._db.add(application_instance)
        self._db.flush()  # Force the returned AI to have an ID

        return application_instance

    def update_from_lti_params(self, application_instance, params: LTIParams):
        """
        Update all the LMS-related attributes present in `params`.

        If the current instance already has a `tool_consumer_instance_guid`
        report it on logging and don't update any of the columns.
        """

        tool_consumer_instance_guid = params.get("tool_consumer_instance_guid")
        if not tool_consumer_instance_guid:
            # guid identifies the rest of the LMS data, if not there skip any
            # updates
            return

        application_instance.check_guid_aligns(tool_consumer_instance_guid)

        # Make sure this application instance is associated with an org.
        self._organization_service.auto_assign_organization(application_instance)

        for attr in [
            "tool_consumer_info_product_family_code",
            "tool_consumer_instance_description",
            "tool_consumer_instance_url",
            "tool_consumer_instance_name",
            "tool_consumer_instance_contact_email",
            "tool_consumer_instance_guid",
            "tool_consumer_info_version",
            "custom_canvas_api_domain",
        ]:
            setattr(application_instance, attr, params.get(attr))

        # This is a potentially misleading, as we can get here from deep-linked
        # "launches". Depending on whether you count that as a launch or not.
        application_instance.last_launched = datetime.now()


def factory(_context, request):
    return ApplicationInstanceService(
        db=request.db,
        aes_service=request.find_service(AESService),
        organization_service=request.find_service(OrganizationService),
    )
