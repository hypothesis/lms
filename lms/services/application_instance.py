from functools import lru_cache

from lms.models import ApplicationInstance
from lms.services import ConsumerKeyError


class ApplicationInstanceService:
    def __init__(self, db, default_consumer_key):
        self._db = db
        self._default_consumer_key = default_consumer_key

    @lru_cache
    def get(self, consumer_key=None) -> ApplicationInstance:
        """
        Return the ApplicationInstance with the given consumer_key.

        If no consumer_key is given return the current request's
        ApplicationInstance (the ApplicationInstance whose consumer_key matches
        request.lti_user.oauth_consumer_key).

        :raise ConsumerKeyError: if the consumer_key isn't in the database
        """
        consumer_key = consumer_key or self._default_consumer_key

        application_instance = self.get_by_consumer_key(consumer_key)

        if application_instance is None:
            raise ConsumerKeyError()

        return application_instance

    def get_by_consumer_key(self, consumer_key):
        """Return the ApplicationInstance with the given consumer_key or None."""

        # TODO - Inline into get?
        return (
            self._db.query(ApplicationInstance)
            .filter_by(consumer_key=consumer_key)
            .one_or_none()
        )

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
    consumer_key = request.lti_user.oauth_consumer_key if request.lti_user else None
    return ApplicationInstanceService(request.db, consumer_key)
