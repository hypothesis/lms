from urllib.parse import unquote
import marshmallow

from marshmallow import EXCLUDE, Schema, ValidationError, fields, post_load
from marshmallow.validate import OneOf

from lms.validation._base import PyramidRequestSchema
from lms.validation._exceptions import LTIToolRedirect

from lms.validation._lti import (
    LTI11BasicLTILaunchSchema,
    LTI13BasicLTILaunchSchema,
    CommonLTILaunchSchema,
)


class BasicLTILaunchSchema(LTI11BasicLTILaunchSchema, PyramidRequestSchema):
    """
    Schema for basic LTI launch requests (i.e. assignment launches).

    This *DOES NOT* contain all of the fields required for authentication.
    For that see `lms.validation.authentication.LaunchParamsAuthSchema`
    """

    location = "form"

    class URLSchema(Schema):
        """Schema containing only validation for the return URL."""

        class Meta:
            """Allow other values, as we are only here to validate the URL."""

            unknown = EXCLUDE

        launch_presentation_return_url = fields.URL()

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

    @marshmallow.pre_load
    def _decode_jwt(self, data, **_kwargs):
        if data["id_token"] == marshmallow.missing:
            raise marshmallow.ValidationError(
                "Missing data for required field.", "id_token"
            )

        jwt_data = self.context["request"].lti_jwt
        try:
            return LTI13BasicLTILaunchSchema().load(jwt_data)
        except Exception as ex:
            print(ex.__dict__)
            raise


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

    @marshmallow.pre_load
    def _decode_jwt(self, data, **_kwargs):
        if data["id_token"] == marshmallow.missing:
            raise marshmallow.ValidationError(
                "Missing data for required field.", "id_token"
            )

        jwt_data = self.context["request"].lti_jwt
        try:
            data = LTI13BasicLTILaunchSchema().load(jwt_data)
            data["url"] = self.context["request"].params["url"]
            return data
        except Exception as ex:
            print(ex.__dict__)
            raise


class ContentItemSelectionLTILaunchSchema(CommonLTILaunchSchema):
    """Schema for content item selection LTI launches."""

    lti_message_type = fields.Str(
        validate=OneOf(["ContentItemSelectionRequest"]), required=True
    )
