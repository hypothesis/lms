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

        application_instance = ApplicationInstance.get_by_consumer_key(
            self._db, consumer_key
        )

        if application_instance is None:
            raise ConsumerKeyError()

        return application_instance

    @staticmethod
    def update_settings(ai, canvas_sections_enabled=None, canvas_groups_enabled=None):
        """
        Update ApplicationInstance.settings.

        For not-nullable values only changes the params passed with a not-None value
        """
        if canvas_sections_enabled is not None:
            ai.settings.set("canvas", "sections_enabled", canvas_sections_enabled)

        if canvas_groups_enabled is not None:
            ai.settings.set("canvas", "groups_enabled", canvas_groups_enabled)

        return ai


def factory(_context, request):
    if request.lti_user:
        consumer_key = request.lti_user.oauth_consumer_key
    else:
        consumer_key = None

    return ApplicationInstanceService(request.db, consumer_key)
