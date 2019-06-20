"""Shared base class for validation schemas to inherit from."""
import marshmallow


__all__ = ["BaseSchema"]


class BaseSchema(marshmallow.Schema):
    """A shared base class for validation schemas to inherit from."""

    class Meta:
        """Marshmallow options for this schema."""

        # Silence a strict=False deprecation warning from marshmallow.
        # TODO: Remove this once we've upgraded to marshmallow 3.
        strict = True

    def __init__(self, request):
        super().__init__()

        # Storing context needed for serialization or deserialization in
        # self.context is a marshmallow convention.
        self.context = {"request": request}
