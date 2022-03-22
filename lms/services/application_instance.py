import secrets
from datetime import datetime
from functools import lru_cache

from sqlalchemy.exc import NoResultFound

from lms.models import ApplicationInstance, LTIRegistration
from lms.services.aes import AESService


class ApplicationInstanceNotFound(Exception):
    """The requested ApplicationInstance wasn't found in the database."""


class ApplicationInstanceService:
    def __init__(self, db, request, aes_service):
        self._db = db
        self._request = request
        self._aes_service = aes_service

    @lru_cache(maxsize=1)
    def get_current(self) -> ApplicationInstance:
        """
        Return the the current request's `ApplicationInstance`.

        This is the `ApplicationInstance` with `id` matching
        `request.application_instance_id`.

        :raise ApplicationInstanceNotFound: if there's no matching
            `ApplicationInstance`
        """
        if self._request.lti_user and self._request.lti_user.application_instance_id:
            if application_instance := self._db.query(ApplicationInstance).get(
                self._request.lti_user.application_instance_id
            ):
                return application_instance

        raise ApplicationInstanceNotFound()

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

    @lru_cache
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

    def build_from_lms_url(  # pylint:disable=too-many-arguments
        self, lms_url, email, developer_key, developer_secret, settings
    ):
        """Instantiate ApplicationInstance with lms_url."""
        encrypted_secret = developer_secret
        aes_iv = None

        if developer_secret and developer_key:
            aes_iv = self._aes_service.build_iv()
            encrypted_secret = self._aes_service.encrypt(aes_iv, developer_secret)

        application_instance = ApplicationInstance(
            consumer_key="Hypothesis" + secrets.token_hex(16),
            shared_secret=secrets.token_hex(32),
            lms_url=lms_url,
            requesters_email=email,
            developer_key=developer_key,
            developer_secret=encrypted_secret,
            aes_cipher_iv=aes_iv,
            created=datetime.utcnow(),
            settings=settings,
        )
        self._db.add(application_instance)
        return application_instance


def factory(_context, request):
    return ApplicationInstanceService(
        request.db,
        request,
        request.find_service(AESService),
    )
