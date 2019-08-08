"""Schema for validating LTI launch params."""
from urllib.parse import unquote

import marshmallow

from lms.services import LTILaunchVerificationError
from lms.validation._helpers import PyramidRequestSchema
from lms.values import LTIUser


__all__ = ("LaunchParamsSchema", "URLConfiguredLaunchParamsSchema")


class LaunchParamsSchema(PyramidRequestSchema):
    """
    Schema for LTI launch params.

    Validates and verifies LTI launch params. Usage via webargs::

        >>> from webargs.pyramidparser import parser
        >>>
        >>> schema = LaunchParamsSchema(request)
        >>> parsed_params = parser.parse(schema, request, locations=["form"])

    Or to verify the request and get an :class:`~lms.values.LTIUser`
    from the request's params::

        >>> schema = LaunchParamsSchema(request)
        >>> schema.lti_user()
        LTIUser(user_id='...', ...)
    """

    user_id = marshmallow.fields.Str(required=True)
    roles = marshmallow.fields.Str(required=True)

    oauth_consumer_key = marshmallow.fields.Str(required=True)
    oauth_nonce = marshmallow.fields.Str(required=True)
    oauth_signature = marshmallow.fields.Str(required=True)
    oauth_signature_method = marshmallow.fields.Str(required=True)
    oauth_timestamp = marshmallow.fields.Str(required=True)
    oauth_version = marshmallow.fields.Str(required=True)

    def __init__(self, request):
        super().__init__(request)
        self._launch_verifier = request.find_service(name="launch_verifier")

    def lti_user(self):
        """
        Return an :class:`~lms.values.LTIUser` from the request's launch params.

        :raise ValidationError: if the request isn't a valid LTI launch request

        :rtype: LTIUser
        """
        kwargs = self.parse(locations=["form"])

        return LTIUser(
            kwargs["user_id"], kwargs["oauth_consumer_key"], kwargs.get("roles", "")
        )

    @marshmallow.validates_schema
    def _verify_oauth_1(self, _data):
        """
        Verify the request's OAuth 1 signature, timestamp, etc.

        :raise marshmallow.ValidationError: if the request doesn't have a valid
            OAuth 1 signature
        """
        try:
            self._launch_verifier.verify()
        except LTILaunchVerificationError as err:
            raise marshmallow.ValidationError("Invalid OAuth 1 signature.") from err


class URLConfiguredLaunchParamsSchema(PyramidRequestSchema):
    """
    Schema for an "URL-configured" Basic LTI Launch.

    An URL-configured launch is one where the content URL is provided by a "url"
    launch param.
    """

    url = marshmallow.fields.Str(required=True)

    @marshmallow.post_load
    def _decode_url(self, _data):  # pylint:disable=no-self-use
        # Work around a bug in Canvas's handling of LTI Launch URLs in
        # SpeedGrader launches. In that context, query params get
        # doubly-encoded. This is worked around by detecting when this has
        # happened and decoding the URL a second time.
        #
        # See https://github.com/instructure/canvas-lms/issues/1486
        url = _data["url"]
        if url.lower().startswith("http%3a") or url.lower().startswith("https%3a"):
            url = unquote(url)
            _data["url"] = url
        return _data
