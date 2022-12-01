"""Common marshmallow schemas for the admin pages."""
from marshmallow import fields, missing


class EmptyStringNoneMixin:
    """
    Allows empty string as "missing value".

    Marshmallow doesn't have a clean solution yet to POSTed values
    (that are always present in the request as empty strings)

    Here we convert them explicitly to None

    https://github.com/marshmallow-code/marshmallow/issues/713
    """

    def deserialize(self, value, attr, data, **kwargs):
        # pylint:disable=compare-to-empty-string
        if value == missing or value.strip() == "":
            return None
        return super().deserialize(value, attr, data, **kwargs)


class EmptyStringInt(EmptyStringNoneMixin, fields.Int):
    """Allow empty string as "missing value" instead of failing integer validation."""
