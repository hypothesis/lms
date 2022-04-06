from urllib.parse import unquote

from marshmallow import (
    EXCLUDE,
    Schema,
    ValidationError,
    fields,
    post_load,
    pre_load,
    validates_schema,
)
from marshmallow.validate import OneOf

from lms.models import LTIParams
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
    lis_person_name_given = fields.Str(load_default="")
    lis_person_name_family = fields.Str(load_default="")
    lis_person_name_full = fields.Str(load_default="")
    lis_person_contact_email_primary = fields.Str(load_default="")

    @pre_load
    def _decode_jwt(self, data, **_kwargs):
        """Use the values encoded in the `id_token` JWT if present."""
        if not self.context["request"].lti_jwt:
            return data

        params = LTIParams.from_v13(self.context["request"].lti_jwt)
        # Make the rest of params also accessible to marshmallow in case any are not coming from the JWT
        # eg query parameters
        # This is to make it backwards compatible with schemas that mix LTI
        # parameters with others that belong to the LMS app (eg the `url` parameter).
        params.update(self.context["request"].params)

        return params


class _CommonLTILaunchSchema(LTIV11CoreSchema):
    """Fields common to different types of LTI launches."""

    location = "form"

    context_id = fields.Str(required=True)
    context_title = fields.Str(required=True)
    lti_version = fields.Str(validate=OneOf(["LTI-1p0", "1.3.0"]), required=True)
    oauth_consumer_key = fields.Str(required=False)

    custom_canvas_api_domain = fields.Str()
    custom_canvas_course_id = fields.Str()
    launch_presentation_return_url = fields.Str()
    tool_consumer_info_product_family_code = fields.Str()

    @validates_schema
    def validate_consumer_key(self, data, **_kwargs):  # pylint: disable=no-self-use
        if (
            not data.get("oauth_consumer_key", None)
            and data["lti_version"] == "LTI-1p0"
        ):
            raise ValidationError("Required for LTI1.1", "oauth_consumer_key")


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
    lti_redirect_fields = {
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
                messages.setdefault(field, []).extend(err.messages[field])
            return_url = None

        if return_url:
            reportable_fields = set(messages.keys()) & self.lti_redirect_fields
            if reportable_fields:
                raise LTIToolRedirect(return_url, messages)

        super().handle_error(error, data, many=many, **kwargs)


class URLConfiguredBasicLTILaunchSchema(BasicLTILaunchSchema):
    """Schema for URL-configured basic LTI launches."""

    url = fields.Str(required=True)

    @post_load
    def _decode_url(self, _data, **_kwargs):  # pylint:disable=no-self-use
        # Work around a bug in Canvas's handling of LTI Launch URLs in
        # SpeedGrader launches. In that context, query params get
        # doubly-encoded. This is worked around by detecting when this has
        # happened and decoding the URL a second time.
        #
        # See https://github.com/instructure/canvas-lms/issues/1486
        url = _data["url"]
        if (
            url.lower().startswith("http%3a")
            or url.lower().startswith("https%3a")
            or url.lower().startswith("canvas%3a")
            or url.lower().startswith("vitalsource%3a")
        ):
            url = unquote(url)
            _data["url"] = url

        return _data


class ContentItemSelectionLTILaunchSchema(_CommonLTILaunchSchema):
    """Schema for content item selection LTI launches."""

    lti_message_type = fields.Str(
        validate=OneOf(["ContentItemSelectionRequest"]), required=True
    )


class ConfigureAssignmentSchema(_CommonLTILaunchSchema):
    """Schema for validating requests to the configure_assignment() view."""

    location = "form"

    document_url = fields.Str(required=True)
    resource_link_id = fields.Str(required=True)
    user_id = fields.Str(required=True)
    context_title = fields.Str(required=True)
    group_set = fields.Str(required=False, allow_none=True)
