from sqlalchemy.ext.mutable import MutableDict


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

    def __repr__(self):
        return f"{self.__class__.__name__}({super().__repr__()})"

    def __str__(self):
        return repr(self)
