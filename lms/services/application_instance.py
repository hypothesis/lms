from functools import lru_cache

from lms.models import ApplicationInstance
from lms.services.exceptions import ApplicationInstanceNotFound


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

        :raise ApplicationInstanceNotFound: if there's no ApplicationInstance
            with consumer_key in the database
        """
        consumer_key = consumer_key or self._default_consumer_key

        application_instance = ApplicationInstance.get_by_consumer_key(
            self._db, consumer_key
        )

        if application_instance is None:
            raise ApplicationInstanceNotFound()

        return application_instance


def factory(_context, request):
    consumer_key = request.lti_user.oauth_consumer_key if request.lti_user else None
    return ApplicationInstanceService(request.db, consumer_key)
