from typing import Optional

from lms.models import ApplicationInstance


class ApplicationInstanceService:
    def __init__(self, db):
        self._db = db

    def get(self, consumer_key: str) -> Optional[ApplicationInstance]:
        """Query one ApplicationInstance by consumer_key."""

        return ApplicationInstance.get_by_consumer_key(self._db, consumer_key)

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
