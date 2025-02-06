import json

from marshmallow import (
    EXCLUDE,
    Schema,
    ValidationError,
    fields,
    pre_load,
    validates_schema,
)
from marshmallow.validate import OneOf, Range

from lms.validation._base import PyramidRequestSchema
from lms.validation._exceptions import LTIToolRedirect


class LTIV11CoreSchema(PyramidRequestSchema):
    """
    Base class for all LTI related schemas.

    We use the LTI 1.1 names in the schemas
    and rely on models.LTIParams for the v13 name translation.
    """

    class Meta:
        unknown = EXCLUDE

    user_id = fields.Str(required=True)
    roles = fields.Str(required=True)
    tool_consumer_instance_guid = fields.Str(required=True)
    lis_person_name_given = fields.Str(load_default="", allow_none=True)
    lis_person_name_family = fields.Str(load_default="", allow_none=True)
    lis_person_name_full = fields.Str(load_default="", allow_none=True)
    lis_person_contact_email_primary = fields.Str(load_default="", allow_none=True)

    @pre_load
    def _decode_jwt(self, data, **_kwargs):
        """Use the values encoded in the `id_token` JWT if present."""
        if not self.context["request"].lti_jwt:
            return data

        params = self.context["request"].lti_params
        # Make the rest of params also accessible to marshmallow in case any are not coming from the JWT
        # eg query parameters
        # This is to make it backwards compatible with schemas that mix LTI
        # parameters with others that belong to the LMS app (eg the `url` parameter).
        params.update(self.context["request"].params)

        return params


class _CommonLTILaunchSchema(LTIV11CoreSchema):
    """Fields common to different types of LTI launches."""

    location = "json_or_form"

    context_id = fields.Str(required=True)
    context_title = fields.Str(required=True)
    lti_version = fields.Str(validate=OneOf(["LTI-1p0", "1.3.0"]), required=True)
    oauth_consumer_key = fields.Str(required=False)

    custom_canvas_course_id = fields.Str()
    launch_presentation_return_url = fields.Str()
    tool_consumer_info_product_family_code = fields.Str()

    @validates_schema
    def validate_consumer_key(self, data, **_kwargs):
        if (
            not data.get("oauth_consumer_key", None)
            and data["lti_version"] == "LTI-1p0"
        ):
            raise ValidationError("Required for LTI1.1", "oauth_consumer_key")  # noqa: EM101, TRY003


class BasicLTILaunchSchema(_CommonLTILaunchSchema):
    """
    Schema for basic LTI launch requests (i.e. assignment launches).

    This *DOES NOT* contain all of the fields required for authentication.
    For that see `lms.validation.authentication.LTI11AuthSchema`
    """

    class URLSchema(Schema):
        """Schema containing only validation for the return URL."""

        class Meta:
            """Allow other values, as we are only here to validate the URL."""

            unknown = EXCLUDE

        launch_presentation_return_url = fields.URL()

    lti_message_type = fields.Str(
        validate=OneOf(["basic-lti-launch-request", "LtiResourceLinkRequest"]),
        required=True,
    )
    resource_link_id = fields.Str(required=True)

    # If we have an error in one of these fields we should redirect back to
    # the calling LMS if possible
    lti_redirect_fields = {  # noqa: RUF012
        "resource_link_id",
        "lti_version",
        "lti_message_type",
        "context_id",
        "context_title",
    }

    def handle_error(self, error, data, *, many, **kwargs):
        """
        Handle validation errors including LTI redirects.

        Certain validation errors require us to redirect back to the tool
        consumer (the LMS calling us) when we detect them.

        This function is called by marshmallow as part of it's error
        processing.

        :raise LTIToolRedirect: If a redirect is possible
        :raise ValidationError: If other validation errors
        """
        messages = error.messages

        try:
            # Extract the launch_presentation_return_url and check it's a real
            # URL
            return_url = (
                BasicLTILaunchSchema.URLSchema()
                .load(data)
                .get("launch_presentation_return_url")
            )
        except ValidationError as err:
            # Update ``messages`` with the error messages from
            # ``err.messages``, but without overwriting any of the existing
            # error messages already present in ``messages``.
            for field in err.messages:
                messages.setdefault(field, []).extend(err.messages[field])  # type:ignore  # noqa: PGH003
            return_url = None

        if return_url:
            reportable_fields = set(messages.keys()) & self.lti_redirect_fields
            if reportable_fields:
                raise LTIToolRedirect(return_url, messages)

        super().handle_error(error, data, many=many, **kwargs)


class DeepLinkingLTILaunchSchema(_CommonLTILaunchSchema):
    """Schema for deep linking LTI launches."""

    lti_message_type = fields.Str(
        validate=OneOf(["ContentItemSelectionRequest", "LtiDeepLinkingRequest"]),
        required=True,
    )

    content_item_return_url = fields.Str(required=True)


class AutoGradingConfigSchema(Schema):
    """Schema for the auto grading options for an assignment."""

    grading_type = fields.Str(
        required=True, validate=OneOf(["all_or_nothing", "scaled"])
    )
    activity_calculation = fields.Str(
        required=True, validate=OneOf(["cumulative", "separate"])
    )

    required_annotations = fields.Int(required=True, validate=Range(min=0))
    required_replies = fields.Int(
        required=False, allow_none=True, validate=Range(min=0)
    )


class ConfigureAssignmentSchema(_CommonLTILaunchSchema):
    """Schema for validating requests to the configure_assignment() view."""

    location = "form"

    document_url = fields.Str(required=True)
    resource_link_id = fields.Str(required=True)
    user_id = fields.Str(required=True)
    context_title = fields.Str(required=True)
    group_set = fields.Str(required=False, allow_none=True)
    auto_grading_config = fields.Nested(
        AutoGradingConfigSchema, required=False, allow_none=True
    )

    @pre_load
    def _load_auto_grading_config(self, data, **_kwargs):
        """Load auto grading config.

        "form" location doesn't accept Nested fields we'll accept the value as json and deserilize it here.
        """
        auto_grading_config = data.get("auto_grading_config")

        if auto_grading_config and isinstance(auto_grading_config, str):
            try:
                data["auto_grading_config"] = json.loads(auto_grading_config)
            except json.decoder.JSONDecodeError as exc:
                raise ValidationError(  # noqa: TRY003
                    "Invalid json for nested field",
                    "auto_grading_config",
                ) from exc

        return data
