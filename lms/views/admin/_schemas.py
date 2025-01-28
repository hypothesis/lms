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
        if value == missing or value.strip() == "":
            return None
        return super().deserialize(value, attr, data, **kwargs)  # type:ignore  # noqa: PGH003


class EmptyStringInt(EmptyStringNoneMixin, fields.Int):  # type: ignore  # noqa: PGH003
    """Allow empty string as "missing value" instead of failing integer validation."""
