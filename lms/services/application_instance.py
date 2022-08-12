import secrets
from datetime import datetime
from functools import lru_cache
from typing import List

from sqlalchemy.exc import NoResultFound

from lms.models import ApplicationInstance, LTIParams, LTIRegistration
from lms.services.aes import AESService
from lms.services.organization import OrganizationService


class ApplicationInstanceNotFound(Exception):
    """The requested ApplicationInstance wasn't found in the database."""


class ApplicationInstanceService:
    def __init__(
        self,
        db,
        request,
        aes_service: AESService,
        organization_service: OrganizationService,
    ):
        self._db = db
        self._request = request
        self._aes_service = aes_service
        self._organization_service = organization_service

    @lru_cache(maxsize=1)
    def get_current(self) -> ApplicationInstance:
        """
        Return the current request's `ApplicationInstance`.

        This is the `ApplicationInstance` with `id` matching
        `request.application_instance_id`.

        :raise ApplicationInstanceNotFound: if there's no matching
            `ApplicationInstance`
        """
        if self._request.lti_user and self._request.lti_user.application_instance_id:
            return self.get_by_id(self._request.lti_user.application_instance_id)

        raise ApplicationInstanceNotFound()

    @lru_cache(maxsize=1)
    def get_by_id(self, id_) -> ApplicationInstance:
        try:
            return self._db.query(ApplicationInstance).filter_by(id=id_).one()
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
            return (
                self._db.query(ApplicationInstance)
                .filter_by(consumer_key=consumer_key)
                .one()
            )
        except NoResultFound as err:
            raise ApplicationInstanceNotFound() from err

    @lru_cache(maxsize=128)
    def get_by_deployment_id(
        self, issuer: str, client_id: str, deployment_id: str
    ) -> ApplicationInstance:
        if not all([issuer, client_id, deployment_id]):
            raise ApplicationInstanceNotFound()

        try:
            return (
                self._db.query(ApplicationInstance)
                .join(LTIRegistration)
                .filter(
                    LTIRegistration.issuer == issuer,
                    LTIRegistration.client_id == client_id,
                    ApplicationInstance.deployment_id == deployment_id,
                )
                .one()
            )
        except NoResultFound as err:
            raise ApplicationInstanceNotFound() from err

    def search(
        self,
        *,
        consumer_key=None,
        issuer=None,
        client_id=None,
        deployment_id=None,
        tool_consumer_instance_guid=None,
    ) -> List[ApplicationInstance]:
        """Return the instances that match all of the passed parameters."""

        query = self._db.query(ApplicationInstance).outerjoin(LTIRegistration)
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

        return query.all()

    def create_application_instance(  # pylint:disable=too-many-arguments
        self,
        lms_url,
        email,
        developer_key,
        developer_secret,
        settings=None,
        deployment_id=None,
        lti_registration_id=None,
    ):
        """Create an ApplicationInstance."""
        consumer_key = (
            "Hypothesis" + secrets.token_hex(16) if not deployment_id else None
        )

        if developer_secret and developer_key:
            aes_iv = self._aes_service.build_iv()
            encrypted_secret = self._aes_service.encrypt(aes_iv, developer_secret)
        else:
            # If either one of developer_key or developer_secret is missing, then we
            # don't save the other one either.
            developer_key = encrypted_secret = developer_secret = aes_iv = None

        application_instance = ApplicationInstance(
            consumer_key=consumer_key,
            shared_secret=secrets.token_hex(32),
            lms_url=lms_url,
            requesters_email=email,
            developer_key=developer_key,
            developer_secret=encrypted_secret,
            aes_cipher_iv=aes_iv,
            created=datetime.utcnow(),
            settings=settings or {},
            deployment_id=deployment_id,
            lti_registration_id=lti_registration_id,
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


def factory(_context, request):
    return ApplicationInstanceService(
        db=request.db,
        request=request,
        aes_service=request.find_service(AESService),
        organization_service=request.find_service(OrganizationService),
    )
