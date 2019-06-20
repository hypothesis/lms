"""Base classes for validation schemas."""
import marshmallow


__all__ = ["PyramidRequestSchema"]


class _BaseSchema(marshmallow.Schema):
    """Base class for all schemas."""

    class Meta:
        """Marshmallow options for all schemas."""

        # Silence a strict=False deprecation warning from marshmallow.
        # TODO: Remove this once we've upgraded to marshmallow 3.
        strict = True


class PyramidRequestSchema(_BaseSchema):
    """Base class for schemas that validate Pyramid requests."""

    def __init__(self, request):
        super().__init__()

        # Storing context needed for serialization or deserialization in
        # self.context is a marshmallow convention.
        self.context = {"request": request}
