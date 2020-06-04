from functools import lru_cache

from Crypto.Cipher import AES

from lms import models
from lms.services import ConsumerKeyError

__all__ = ["ApplicationInstanceGetter"]


class ApplicationInstanceGetter:
    """Methods for getting properties from application instances."""

    def __init__(self, db, aes_secret, consumer_key, section_groups_feature_flag):
        self._db = db
        self._aes_secret = aes_secret
        self._consumer_key = consumer_key
        self._section_groups_feature_flag = section_groups_feature_flag

    def developer_key(self):
        """
        Return the Canvas developer key for the current request, or None.

        :raise ConsumerKeyError: if the request's consumer key isn't in the DB

        :return: the matching Canvas API developer key or ``None``
        :rtype: str or ``None``
        """
        return self._get_by_consumer_key().developer_key

    def developer_secret(self):
        """
        Return the Canvas developer secret for the current request or None.

        :raise ConsumerKeyError: if the request's consumer key isn't in the DB

        :return: the matching Canvas API developer secret or ``None``
        :rtype: str or ``None``
        """
        application_instance = self._get_by_consumer_key()

        if application_instance.developer_secret is None:
            return None

        cipher = AES.new(
            self._aes_secret, AES.MODE_CFB, application_instance.aes_cipher_iv
        )
        return cipher.decrypt(application_instance.developer_secret)

    def lms_url(self):
        """
        Return the LMS URL for the current request.

        :raise ConsumerKeyError: if the request's consumer key isn't in the DB

        :return: the matching LMS URL
        :rtype: str
        """
        return self._get_by_consumer_key().lms_url

    def provisioning_enabled(self):
        """
        Return ``True`` if provisioning is enabled for the current request.

        Return ``True`` if the provisioning feature is enabled for the current
        request, ``False`` otherwise.
        """
        try:
            provisioning = self._get_by_consumer_key().provisioning
        except ConsumerKeyError:
            provisioning = False
        return provisioning

    def canvas_sections_supported(self):
        """Return True if the application instance has Canvas sections is enabled."""
        if not self._section_groups_feature_flag:
            return False

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
    return ApplicationInstanceGetter(
        request.db,
        request.registry.settings["aes_secret"],
        request.lti_user.oauth_consumer_key,
        section_groups_feature_flag=request.feature("section_groups"),
    )
