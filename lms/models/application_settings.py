import base64
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import InstrumentedAttribute


class ApplicationSettings(MutableDict):
    """
    Model for accessing and updating application settings.

    This is a dict subclass, but you should use the custom get() and set()
    methods below to get and set values because they're safer and more
    convenient.

    If you mutate a nested dict or list in-place this change won't be detected
    by SQLAlchemy and your change **will not be saved**.

    For example in the code below the change to "sections_enabled" will not be
    saved when the transaction is committed:

    >>> ai = db.query(models.ApplicationInstance).filter_by(...).one()
    >>> ai.settings["canvas"]["sections_enabled"] = False

    The safe thing to do is to use the custom set() method because it makes
    sure that your changes are saved.

    But alternatively you can call changed() after making your changes, then
    they will be saved. In this example the changes to both "sections_enabled"
    and "bar" will be saved:

    >>> ai = db.query(models.ApplicationInstance).filter_by(...).one()
    >>> ai.settings["canvas"]["sections_enabled"] = False
    >>> ai.settings["foo"]["bar"] = "gar"
    >>> # Notify SQLAlchemy that ai.settings has changed so it knows to save it.
    >>> ai.settings.changed()
    """

    def get(self, group, key, default=None):
        """
        Return the requested setting or None.

        Will return None if *either* "group" or "key" is missing from the dict or the value of `default`

        :param group: The name of the group of settings
        :param key: The key in that group
        :param default: Default value if the group/key combiantion is missing
        :return: The value or None
        """
        return super().get(group, {}).get(key, default)

    def set(self, group, key, value):
        """
        Set a specific setting in a group.

        Will create the sub-dict "group" for you if it's missing from the dict,
        and will notify SQLAlchemy of your change so that it gets saved to the
        DB.

        :param group: The name of the group of settings
        :param key: The key in that group
        :param value: The value to set
        """
        super().setdefault(group, {})[key] = value

    def set_secret(self, aes_service, group, key, value: str):
        """
        Store a setting as a secret.

        Store the setting AES encrypted.

        :param aes_service: AESService to encrypt the string
        :param group: The name of the group of settings
        :param key: The key in that group
        :param value: The value to set
        """
        aes_iv = aes_service.build_iv()
        value = aes_service.encrypt(aes_iv, value)

        # Store both the setting and the IV
        # We can't store the bytes directly in JSON so we store it as base64
        super().setdefault(group, {})[key] = base64.b64encode(value).decode("utf-8")
        super().setdefault(group, {})[f"{key}_aes_iv"] = base64.b64encode(
            aes_iv
        ).decode("utf-8")

    def get_secret(self, aes_service, group, key) -> Optional[str]:
        """
        Get a secret setting.

        :param aes_service: AESService to decrypt the string
        :param group: The name of the group of settings
        :param key: The key in that group
        """
        value = super().get(group, {}).get(key)
        if not value:
            return None

        aes_value = base64.b64decode(value)
        aes_iv = base64.b64decode(super().get(group, {}).get(f"{key}_aes_iv"))

        return aes_service.decrypt(aes_iv, aes_value).decode("utf-8")

    @classmethod
    def matching(cls, column: InstrumentedAttribute, spec: dict):
        """
        Return a clause to filter an SQLAlchemy query.

        This method accepts a match dict which should have keys like this:

            {
                # Specify an exact key should have an exact value
                "group.key": "exact_value_to_match"
                # Specify an exact key should exist
                "group.key": ...
                # Specify a group should exist
                "group": ...
            }

        :param column: The column to apply this to
        :param spec: The filter specification as described above
        """
        clauses = []

        for joined_key, value in spec.items():
            group, key = (
                joined_key.split(".") if "." in joined_key else (joined_key, None)
            )

            if key is None:
                clauses.append(column.has_key(group))

            elif value is not ...:
                clauses.append(column.contains({group: {key: value}}))
            else:
                clauses.append(column[group].has_key(key))

        return sa.and_(*clauses)

    def __repr__(self):
        return f"{self.__class__.__name__}({super().__repr__()})"

    def __str__(self):
        return repr(self)
