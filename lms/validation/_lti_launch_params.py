from urllib.parse import unquote

import marshmallow
from marshmallow import EXCLUDE, Schema, ValidationError, fields, post_load
from marshmallow.validate import OneOf

from lms.validation._base import PyramidRequestSchema
from lms.validation._exceptions import LTIToolRedirect


class _CommonLTILaunchSchema(PyramidRequestSchema):
    """Fields common to different types of LTI launches."""

    location = "form"

    context_id = fields.Str(required=True)
    context_title = fields.Str(required=True)
    lti_version = fields.Str(validate=OneOf(["LTI-1p0", "1.3.0"]), required=True)
    oauth_consumer_key = fields.Str(required=False)  # TODO validate required for 1.1
    tool_consumer_instance_guid = fields.Str(required=True)
    user_id = fields.Str(required=True)

    custom_canvas_api_domain = fields.Str()
    custom_canvas_course_id = fields.Str()
    launch_presentation_return_url = fields.Str(allow_none=True)
    lis_person_name_full = fields.Str()
    lis_person_name_family = fields.Str()
    lis_person_name_given = fields.Str()
    tool_consumer_info_product_family_code = fields.Str()

    @marshmallow.pre_load
    def _decode_jwt(self, data, **_kwargs):
        if not self.context["request"].jwt_params:
            return data

        jwt_params = self.context["request"].jwt_params

        data["tool_consumer_instance_guid"] = jwt_params[
            "https://purl.imsglobal.org/spec/lti/claim/tool_platform"
        ]["guid"]
        data["user_id"] = jwt_params["sub"]

        data["lis_person_name_given"] = jwt_params["given_name"]
        data["lis_person_name_family"] = jwt_params["family_name"]
        data["lis_person_name_full"] = jwt_params["name"]

        data["tool_consumer_info_product_family_code"] = jwt_params[
            "https://purl.imsglobal.org/spec/lti/claim/tool_platform"
        ]["product_family_code"]
        data["launch_presentation_return_url"] = jwt_params.get(
            "https://purl.imsglobal.org/spec/lti/claim/launch_presentation", {}
        ).get("return_url", None)

        if custom := jwt_params.get("https://purl.imsglobal.org/spec/lti/claim/custom"):
            data["custom_canvas_api_domain"] = custom.get("canvas_api_domain")
            data["custom_canvas_course_id"] = str(custom.get("canvas_course_id"))

        data["context_id"] = jwt_params[
            "https://purl.imsglobal.org/spec/lti/claim/context"
        ]["id"]
        data["context_title"] = jwt_params[
            "https://purl.imsglobal.org/spec/lti/claim/context"
        ]["title"]

        data["lti_version"] = jwt_params[
            "https://purl.imsglobal.org/spec/lti/claim/version"
        ]

        return data


class BasicLTILaunchSchema(_CommonLTILaunchSchema):
    """
    Schema for basic LTI launch requests (i.e. assignment launches).

    This *DOES NOT* contain all of the fields required for authentication.
    For that see `lms.validation.authentication.LaunchParamsAuthSchema`
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

    @marshmallow.pre_load
    def _decode_jwt(self, data, **kwargs):
        data = super()._decode_jwt(data, **kwargs)
        if not self.context["request"].jwt_params:
            return data

        jwt_params = self.context["request"].jwt_params

        data["lti_message_type"] = jwt_params[
            "https://purl.imsglobal.org/spec/lti/claim/message_type"
        ]

        data["resource_link_id"] = jwt_params[
            "https://purl.imsglobal.org/spec/lti/claim/resource_link"
        ]["id"]

        return data


class URLConfiguredBasicLTILaunchSchema(BasicLTILaunchSchema):
    """Schema for URL-configured basic LTI launches."""

    url = fields.Str(required=True)

    @marshmallow.pre_load
    def _decode_jwt(self, data, **kwargs):
        data = super()._decode_jwt(data, **kwargs)

        if not self.context["request"].jwt_params:
            return data

        jwt_params = self.context["request"].jwt_params

        # This seems wrong, shound't we get a message in the jwt token with the configued deep linking assigment
        data["url"] = self.context["request"].params["url"]

        return data

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
        validate=OneOf(["ContentItemSelectionRequest", "LtiDeepLinkingRequest"]),
        required=True,
    )

    content_item_return_url = fields.Str(required=True)

    @marshmallow.pre_load
    def _decode_jwt(self, data, **kwargs):
        data = super()._decode_jwt(data, **kwargs)
        if not self.context["request"].jwt_params:
            return data

        jwt_params = self.context["request"].jwt_params

        data["lti_message_type"] = jwt_params[
            "https://purl.imsglobal.org/spec/lti/claim/message_type"
        ]
        data["content_item_return_url"] = jwt_params[
            "https://purl.imsglobal.org/spec/lti-dl/claim/deep_linking_settings"
        ]["deep_link_return_url"]

        return data
