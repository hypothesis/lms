"""Validation for OAuth views."""
import marshmallow
from webargs import fields


class CanvasOAuthCallbackSchema(marshmallow.Schema):
    """Schema for validating OAuth 2 redirect_uri requests from Canvas."""

    code = fields.Str(required=True)
    state = fields.Str(required=True)

    class Meta:
        """Marshmallow options for this schema."""

        # Silence a strict=False deprecation warning from marshmallow.
        # TODO: Remove this once we've upgraded to marshmallow 3.
        strict = True
