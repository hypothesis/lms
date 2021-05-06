from functools import lru_cache

from lms import models
from lms.services import ConsumerKeyError

__all__ = ["ApplicationInstanceGetter"]


class ApplicationInstanceGetter:
    """Methods for getting properties from application instances."""

    def __init__(self, db, consumer_key):
        self._db = db
        self._consumer_key = consumer_key

    def developer_key(self):
        """
        Return the Canvas developer key for the current request, or None.

        :raise ConsumerKeyError: if the request's consumer key isn't in the DB

        :return: the matching Canvas API developer key or ``None``
        :rtype: str or ``None``
        """
        return self._get_by_consumer_key().developer_key

    def lms_url(self):
        """
        Return the LMS URL for the current request.

        :raise ConsumerKeyError: if the request's consumer key isn't in the DB

        :return: the matching LMS URL
        :rtype: str
        """
        return self._get_by_consumer_key().lms_url

    def canvas_sections_supported(self):
        """Return True if the application instance has Canvas sections is enabled."""
        try:
            app_instance = self._get_by_consumer_key()
        except ConsumerKeyError:
            return False

        # We need a developer key to call the API
        return bool(app_instance.developer_key)

    def settings(self):
        return self._get_by_consumer_key().settings

    def shared_secret(self):
        """
        Return the LTI/OAuth 1 shared secret for the current request.

        This is called the ``oauth_consumer_secret`` in the OAuth 1.0 spec.

        :raise ConsumerKeyError: if the request's consumer key isn't in the DB

        :return: the request's shared secret
        :rtype: str
        """
        return self._get_by_consumer_key().shared_secret

    @lru_cache(maxsize=1)
    def _get_by_consumer_key(self):
        """
        Return the ApplicationInstance with the given consumer_key or ``None``.

        :raise ConsumerKeyError: if the consumer key isn't in the database

        :return: the matching ApplicationInstance or ``None``
        :rtype: :cls:`lms.models.ApplicationInstance` or ``None``
        """
        application_instance = models.ApplicationInstance.get_by_consumer_key(
            self._db, self._consumer_key
        )

        if application_instance is None:
            raise ConsumerKeyError()

        return application_instance


def application_instance_getter_service_factory(_context, request):
    return ApplicationInstanceGetter(request.db, request.lti_user.oauth_consumer_key)
