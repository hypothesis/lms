import base64
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum, member
from typing import Any

import sqlalchemy as sa
from pyramid.settings import asbool
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import InstrumentedAttribute


class SettingFormat(Enum):
    """Valid values for JSONSetting.format.

    Not that some of these values double as an identifier and a function `f(str) -> Any` to convert strings to the right JSON value (eg. asbool)
    while other are just mere identifiers (AES_SECRET).
    """

    BOOLEAN = member(asbool)
    """Regular True/False boolean. Convert it from strings using pyramid's asbool function"""

    TRI_STATE = member(lambda value: None if value == "none" else asbool(value))
    """Tri state True/False/None. Use "none" for the third state, pass the value to asbool otherwise.

    In settings the third value is meant to represent "unset" or "default"
    """

    AES_SECRET = object()  # Helper to declare settings as secret.

    STRING = str


@dataclass(init=False)
class JSONSetting:
    """Describe a permitted field in a JSONSettings object."""

    group: str
    """The group name that this setting is a part of."""

    key: str
    """The key within the group that this setting is a part of."""

    format: SettingFormat = SettingFormat.STRING
    """An identifier to say what type of field this is."""

    default: Any = None

    def __init__(
        self,
        compound_key: str,
        format_: SettingFormat = SettingFormat.STRING,
        default=None,
    ):
        self.group, self.key = compound_key.split(".")
        self.format = format_
        self.default = default

    @property
    def compound_key(self) -> str:
        """Get the group and key as a single value."""
        return f"{self.group}.{self.key}"


class JSONSettings(MutableDict):
    """
    Model for accessing and updating settings stored as JSON.

    This is a dict subclass, but you should use the custom get() and set()
    methods below to get and set values because they're safer and more
    convenient.

    If you mutate a nested dict or list in-place this change won't be detected
    by SQLAlchemy and your change **will not be saved**.

    For example in the code below the change to "sections_enabled" will not be
    saved when the transaction is committed:

    >>> model.settings["canvas"]["sections_enabled"] = False

    The safe thing to do is to use the custom set() method because it makes
    sure that your changes are saved.

    But alternatively you can call changed() after making your changes, then
    they will be saved. In this example the changes to both "sections_enabled"
    and "bar" will be saved:

    >>> model.settings["canvas"]["sections_enabled"] = False
    >>> model.settings["foo"]["bar"] = "gar"
    >>> # Notify SQLAlchemy that settings have changed, so it knows to save it.
    >>> model.settings.changed()
    """

    fields: Mapping[Any, JSONSetting] | None = None
    """
    An optional spec for the acceptable fields and types.
    """

    def get(self, group: str, key: str, default=None):  # type: ignore[override]
        """
        Return the requested setting or None.

        Will return None if *either* "group" or "key" is missing from the dict or the value of `default`

        :param group: The name of the group of settings
        :param key: The key in that group
        :param default: Default value if the group/key combination is missing
        :return: The value or None
        """
        return super().get(group, {}).get(key, default)

    def get_setting(self, setting: JSONSetting):
        value = self.get(setting.group, setting.key, setting.default)
        if value is None:  # None is used a sentinel for "unset" or "default"
            value = setting.default

        return value

    def get_raw_setting(self, setting: JSONSetting):
        """Get the value of the setting as is stored on the DB.

        This method for example ignores the default value.
        """

        return super().get(setting.group, {}).get(setting.key)

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

    def set_secret(self, aes_service, group, key, value: str) -> None:
        """
        Store a setting as a secret.

        Store the setting AES encrypted.

        :param aes_service: AESService to encrypt the string
        :param group: The name of the group of settings
        :param key: The key in that group
        :param value: The value to set
        """
        aes_iv = aes_service.build_iv()
        encrypted_value: bytes = aes_service.encrypt(aes_iv, value)

        # Store both the setting and the IV
        # We can't store the bytes directly in JSON so we store it as base64

        super().setdefault(group, {})[key] = base64.b64encode(encrypted_value).decode(
            "utf-8"
        )
        super().setdefault(group, {})[f"{key}_aes_iv"] = base64.b64encode(
            aes_iv
        ).decode("utf-8")

    def get_secret(self, aes_service, group, key) -> str | None:
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
                # Specify an exact key should exist (use ellipsis literal)
                "group.key": ...
                # Specify a group should exist (use ellipsis literal)
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
                # Search for the group to exist, but nothing more
                clauses.append(column.has_key(group))

            elif value is ...:
                # Look for the group and key, with any value
                clauses.append(column[group].has_key(key))

            else:
                # Look for the group and key, with a specific value
                clauses.append(column.contains({group: {key: value}}))

        return sa.and_(*clauses)

    def __repr__(self):
        return f"{self.__class__.__name__}({super().__repr__()})"

    def __str__(self):
        return repr(self)
