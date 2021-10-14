from functools import lru_cache

from sqlalchemy.exc import NoResultFound

from lms.models import ApplicationInstance


class ApplicationInstanceNotFound(Exception):
    """The requested ApplicationInstance wasn't found in the database."""


class ApplicationInstanceService:
    def __init__(self, db, request):
        self._db = db
        self._request = request

    @lru_cache
    def get_current(self) -> ApplicationInstance:
        """
        Return the the current request's `ApplicationInstance`.

        This is the `ApplicationInstance` with `consumer_key` matching
        `request.lti_user.oauth_consumer_key`.

        :raise ApplicationInstanceNotFound: if there's no matching
            `ApplicationInstance`
        """

        if self._request.lti_user:
            return self.get_by_consumer_key(self._request.lti_user.oauth_consumer_key)

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
    return ApplicationInstanceService(request.db, request)
