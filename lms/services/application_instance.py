from typing import Optional

from sqlalchemy import or_

from lms.models import ApplicationInstance


class ApplicationInstanceService:
    def __init__(self, db):
        self._db = db

    def find(self, query: str) -> Optional[ApplicationInstance]:
        """Query an ApplicationInstance by both the unique pk and consumer_key."""
        return (
            self._db.query(ApplicationInstance)
            .filter(
                or_(
                    ApplicationInstance.id == query if query.isdigit() else None,
                    ApplicationInstance.consumer_key == query,
                )
            )
            .one_or_none()
        )

    # pylint: disable=invalid-name
    def get(self, id_: int) -> Optional[ApplicationInstance]:
        """Query an ApplicationInstance by primary key."""

        return self._db.query(ApplicationInstance).get(id_)

    @staticmethod
    def update_settings(
        installation, canvas_sections_enabled=None, canvas_groups_enabled=None
    ):
        """
        Update ApplicationInstance.settings.

        For not nullable values only changes the params passed with a not None value
        """
        if canvas_sections_enabled is not None:
            installation.settings.set(
                "canvas", "sections_enabled", canvas_sections_enabled
            )

        if canvas_groups_enabled is not None:
            installation.settings.set("canvas", "groups_enabled", canvas_groups_enabled)

        return installation


def factory(_context, request):
    return ApplicationInstanceService(
        request.db,
    )
