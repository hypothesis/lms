from sqlalchemy import select
from sqlalchemy.exc import NoResultFound

from lms.models import UserPreferences


class UserPreferencesService:
    def __init__(self, db):
        self._db = db

    def get(self, h_userid: str) -> UserPreferences:
        """Return the user preferences for the given h_userid."""
        try:
            preferences = self._db.scalars(
                select(UserPreferences).where(UserPreferences.h_userid == h_userid)
            ).one()
        except NoResultFound:
            preferences = UserPreferences(h_userid=h_userid, preferences={})
            self._db.add(preferences)

        return preferences

    def set(self, h_userid: str, new_preferences: dict) -> None:
        """Insert the given new_preferences into h_userid's user preferences.

        Existing items will be updated and new items will be created in
        h_userid's user preferences as necessary.
        """
        preferences = self.get(h_userid)

        for key, value in new_preferences.items():
            preferences.preferences[key] = value


def factory(_context, request) -> UserPreferencesService:
    return UserPreferencesService(request.db)
