from Crypto.Cipher import AES
from sqlalchemy.orm.exc import NoResultFound

from lms.services import ConsumerKeyError
from lms.models import ApplicationInstance


__all__ = ["ApplicationInstanceGetter"]


class ApplicationInstanceGetter:
    """Methods for getting properties from application instances."""

    def __init__(self, _context, request):
        self._db = request.db
        self._aes_secret = request.registry.settings["aes_secret"]

    def developer_key(self, consumer_key):
        """
        Return the Canvas developer key for the given consumer_key, or None.

        :arg consumer_key: the consumer key to search for
        :type consumer_key: str

        :raise ConsumerKeyError: if the consumer key isn't in the database

        :return: the matching Canvas API developer key or ``None``
        :rtype: str or ``None``
        """
        return self._get(consumer_key).developer_key

    def developer_secret(self, consumer_key):
        """
        Return the Canvas developer secret for the given consumer_key, or None.

        :arg consumer_key: the consumer key to search for
        :type consumer_key: str

        :raise ConsumerKeyError: if the consumer key isn't in the database

        :return: the matching Canvas API developer secret or ``None``
        :rtype: str or ``None``
        """
        application_instance = self._get(consumer_key)

        if application_instance.developer_secret is None:
            return None

        cipher = AES.new(
            self._aes_secret, AES.MODE_CFB, application_instance.aes_cipher_iv
        )
        return cipher.decrypt(application_instance.developer_secret)

    def lms_url(self, consumer_key):
        """
        Return the LMS URL for the given LTI consumer_key.

        :arg consumer_key: the consumer key to search for
        :type consumer_key: str

        :raise ConsumerKeyError: if the consumer key isn't in the database

        :return: the matching LMS URL
        :rtype: str
        """
        return self._get(consumer_key).lms_url

    def provisioning_enabled(self, consumer_key):
        """
        Return ``True`` if provisioning is enabled for the given consumer key.

        Return ``True`` if the provisioning feature is enabled for the given
        consumer key, ``False`` otherwise.

        :arg consumer_key: the consumer key to search for
        :type consumer_key: str
        """
        try:
            provisioning = self._get(consumer_key).provisioning
        except ConsumerKeyError:
            provisioning = False
        return provisioning

    def shared_secret(self, consumer_key):
        """
        Return the LTI/OAuth 1 shared secret for the given LTI consumer_key.

        This is called the ``oauth_consumer_secret`` in the OAuth 1.0 spec.

        :arg consumer_key: the consumer key to search for
        :type consumer_key: str

        :raise ConsumerKeyError: if the consumer key isn't in the database

        :return: the matching shared secret
        :rtype: str
        """
        return self._get(consumer_key).shared_secret

    def _get(self, consumer_key):
        """
        Return the ApplicationInstance with the given consumer_key or ``None``.

        :arg consumer_key: the consumer key to search for
        :type consumer_key: str

        :raise ConsumerKeyError: if the consumer key isn't in the database

        :return: the matching ApplicationInstance or ``None``
        :rtype: :cls:`lms.models.ApplicationInstance` or ``None``
        """
        try:
            return (
                self._db.query(ApplicationInstance)
                .filter(ApplicationInstance.consumer_key == consumer_key)
                .one()
            )
        except NoResultFound as err:
            raise ConsumerKeyError() from err
