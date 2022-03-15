from functools import lru_cache

from sqlalchemy.exc import NoResultFound

from lms.models import ApplicationInstance
from lms.services.aes import AESService


class ApplicationInstanceNotFound(Exception):
    """The requested ApplicationInstance wasn't found in the database."""


class ApplicationInstanceService:
    def __init__(self, db, request, aes_service):
        self._db = db
        self._request = request
        self._aes_service = aes_service

    @lru_cache
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

    @lru_cache
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


def factory(_context, request):
    return ApplicationInstanceService(
        request.db,
        request,
        request.find_service(AESService),
    )
