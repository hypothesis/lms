from functools import lru_cache

from lms.models import ApplicationInstance
from lms.services import ConsumerKeyError


class ApplicationInstanceService:
    def __init__(self, db, request):
        self._db = db
        self._request = request

    @lru_cache
    def get(self, consumer_key=None) -> ApplicationInstance:
        """
        Return the ApplicationInstance with the given consumer_key.

        If no consumer_key is given return the current request's
        ApplicationInstance (the ApplicationInstance whose consumer_key matches
        request.lti_user.oauth_consumer_key).

        :raise ConsumerKeyError: if the consumer_key isn't in the database
        """
        if not consumer_key:
            consumer_key = (
                self._request.lti_user.oauth_consumer_key
                if self._request.lti_user
                else None
            )

        application_instance = (
            self._db.query(ApplicationInstance)
            .filter_by(consumer_key=consumer_key)
            .one_or_none()
        )

        if application_instance is None:
            raise ConsumerKeyError()

        return application_instance

    def create(  # pylint:disable=too-many-arguments
        self, lms_url, email, developer_key, developer_secret, aes_secret
    ):
        ai = ApplicationInstance(
            lms_url=lms_url,
            requesters_email=email,
            settings={
                "canvas": {"sections_enabled": bool(developer_key and developer_secret)}
            },
        )

        ai.encrypt_developer_secret(developer_key, developer_secret, aes_secret)

        self._db.add(ai)

        return ai


def factory(_context, request):
    return ApplicationInstanceService(request.db, request)
