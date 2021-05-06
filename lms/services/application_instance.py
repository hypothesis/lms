from functools import lru_cache
from typing import Optional

from Cryptodome.Cipher import AES

from lms.models import ApplicationInstance
from lms.services import ConsumerKeyError


class ApplicationInstanceService:
    def __init__(self, aes_secret, db, default_consumer_key):
        self._aes_secret = aes_secret
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

    def developer_secret(self) -> Optional[str]:
        """
        Return the Canvas developer secret for the current request or None.

        :raise ConsumerKeyError: if the request's consumer key isn't in the DB
        """
        application_instance = self.get()

        if application_instance.developer_secret is None:
            return None

        cipher = AES.new(
            self._aes_secret, AES.MODE_CFB, application_instance.aes_cipher_iv
        )
        return cipher.decrypt(application_instance.developer_secret)

    def provisioning_enabled(self):
        """Return True if provisioning is enabled for the current request."""
        try:
            return self.get().provisioning
        except ConsumerKeyError:
            return False

    def canvas_sections_supported(self):
        """Return True if the current request's application instance has Canvas sections enabled."""
        try:
            return bool(self.get().developer_key)
        except ConsumerKeyError:
            return False

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

    return ApplicationInstanceService(
        request.registry.settings["aes_secret"], request.db, consumer_key
    )
