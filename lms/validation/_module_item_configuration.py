"""Validation for the configure_module_item() view."""

from webargs import fields

from lms.validation._helpers import PyramidRequestSchema


__all__ = ["ConfigureModuleItemSchema"]


class ConfigureModuleItemSchema(PyramidRequestSchema):
    """Schema for validating requests to the configure_module_item() view."""

    locations = ["form"]

    document_url = fields.Str(required=True)
    resource_link_id = fields.Str(required=True)
    tool_consumer_instance_guid = fields.Str(required=True)
