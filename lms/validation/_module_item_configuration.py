"""Validation for the configure_module_item() view."""

import marshmallow
from webargs import fields


__all__ = ["ConfigureModuleItemSchema"]


class ConfigureModuleItemSchema(marshmallow.Schema):
    """Schema for validating requests to the configure_module_item() view."""

    document_url = fields.Str(required=True)
    resource_link_id = fields.Str(required=True)
    tool_consumer_instance_guid = fields.Str(required=True)

    class Meta:
        """Marshmallow options for this schema."""

        # Silence a strict=False deprecation warning from marshmallow.
        # TODO: Remove this once we've upgraded to marshmallow 3.
        strict = True

    def __init__(self, request):
        super().__init__()
        self._request = request
