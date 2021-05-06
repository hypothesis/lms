from lms.models import ApplicationInstance
from lms.services import ConsumerKeyError


class ApplicationInstanceService:
    def __init__(self, db):
        self._db = db

    def get(self, consumer_key: str) -> ApplicationInstance:
        """
        Return the ApplicationInstance with the given consumer_key.

        :raise ConsumerKeyError: if the consumer_key isn't in the database
        """

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

        For not nullable values only changes the params passed with a not None value
        """
        if canvas_sections_enabled is not None:
            ai.settings.set("canvas", "sections_enabled", canvas_sections_enabled)

        if canvas_groups_enabled is not None:
            ai.settings.set("canvas", "groups_enabled", canvas_groups_enabled)

        return ai


def factory(_context, request):
    return ApplicationInstanceService(
        request.db,
    )
