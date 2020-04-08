from functools import lru_cache

from Crypto.Cipher import AES
from sqlalchemy.orm.exc import NoResultFound

from lms.models import ApplicationInstance
from lms.services import ConsumerKeyError

__all__ = ["ApplicationInstanceGetter"]


class ApplicationInstanceGetter:
    """Methods for getting properties from application instances."""

    def __init__(self, db, aes_secret, consumer_key):
        self._db = db
        self._aes_secret = aes_secret
        self._consumer_key = consumer_key

    def developer_key(self):
        """
        Return the Canvas developer key for the current request, or None.

        :raise ConsumerKeyError: if the request's consumer key isn't in the DB

        :return: the matching Canvas API developer key or ``None``
        :rtype: str or ``None``
        """
        return self._get().developer_key

    def developer_secret(self):
        """
        Return the Canvas developer secret for the current request or None.

        :raise ConsumerKeyError: if the request's consumer key isn't in the DB

        :return: the matching Canvas API developer secret or ``None``
        :rtype: str or ``None``
        """
        application_instance = self._get()

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
        return self._get().lms_url

    def provisioning_enabled(self):
        """
        Return ``True`` if provisioning is enabled for the current request.

        Return ``True`` if the provisioning feature is enabled for the current
        request, ``False`` otherwise.
        """
        try:
            provisioning = self._get().provisioning
        except ConsumerKeyError:
            provisioning = False
        return provisioning

    def shared_secret(self):
        """
        Return the LTI/OAuth 1 shared secret for the current request.

        This is called the ``oauth_consumer_secret`` in the OAuth 1.0 spec.

        :raise ConsumerKeyError: if the request's consumer key isn't in the DB

        :return: the request's shared secret
        :rtype: str
        """
        return self._get().shared_secret

    @lru_cache(maxsize=1)
    def _get(self):
        """
        Return the ApplicationInstance with the given consumer_key or ``None``.

        :raise ConsumerKeyError: if the consumer key isn't in the database

        :return: the matching ApplicationInstance or ``None``
        :rtype: :cls:`lms.models.ApplicationInstance` or ``None``
        """
        try:
            return (
                self._db.query(ApplicationInstance)
                .filter(ApplicationInstance.consumer_key == self._consumer_key)
                .one()
            )
        except NoResultFound as err:
            raise ConsumerKeyError() from err


def application_instance_getter_service_factory(_context, request):
    return ApplicationInstanceGetter(
        request.db,
        request.registry.settings["aes_secret"],
        request.params.get("oauth_consumer_key"),
    )
